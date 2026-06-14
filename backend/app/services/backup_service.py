import os
import zipfile
import hashlib
import shutil
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.services.process_manager import process_manager
from app.repositories.backup_repo import BackupRepository
from app.models.backup import Backup

# Backups directory is dynamically resolved relative to minecraft server directory

def build_zip_file(zip_filepath: str, server_dir: str, jar_name: str) -> str:
    sha256 = hashlib.sha256()
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(server_dir):
            # Prune cache, logs, and bundler folders from recursion
            dirs[:] = [d for d in dirs if d not in ('cache', 'logs', 'bundler')]
            for file in files:
                if file == jar_name:
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, server_dir)
                zipf.write(file_path, arcname)
                
                # Stream file into SHA256 hashing
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(65536), b''):
                        sha256.update(chunk)
    return sha256.hexdigest()

def purge_server_directory(server_dir: str, jar_name: str):
    for entry in os.listdir(server_dir):
        if entry in (jar_name, "logs", "cache", "bundler"):
            continue
        path = os.path.join(server_dir, entry)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

def extract_zip_file(zip_filepath: str, server_dir: str):
    with zipfile.ZipFile(zip_filepath, 'r') as zipf:
        zipf.extractall(server_dir)

class BackupService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BackupService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @property
    def backups_dir(self) -> str:
        path = os.path.abspath(os.path.join(settings.MINECRAFT_SERVER_DIR, "..", "backups"))
        os.makedirs(path, exist_ok=True)
        return path

    def __init__(self):
        if not hasattr(self, "_initialized"):
            # Ensure directory exists on initialize
            _ = self.backups_dir
            self._initialized = True

    async def create_backup(self, db: AsyncSession, user_id: int | None = None) -> Backup:
        # Create a pending backup record
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename_temp = f"backup_{timestamp_str}.zip"
        filepath_temp = os.path.join(self.backups_dir, filename_temp)

        backup = await BackupRepository.create(
            db=db,
            filename=filename_temp,
            filepath=filepath_temp,
            file_size=0,
            checksum="pending",
            status="PENDING",
            created_by=user_id
        )

        is_running = process_manager.status == "RUNNING"
        
        try:
            if is_running:
                # Flush save buffers and disable active world writing
                await process_manager.write_stdin("save-off")
                await process_manager.write_stdin("save-all")
                await asyncio.sleep(2) # Give server thread a window to commit chunks

            # Build zip file in worker thread
            checksum = await asyncio.to_thread(
                build_zip_file,
                filepath_temp,
                settings.MINECRAFT_SERVER_DIR,
                settings.MINECRAFT_JAR_NAME
            )

            file_size = os.path.getsize(filepath_temp)

            # Update database record
            backup.checksum = checksum
            backup.file_size = file_size
            backup.status = "SUCCESSFUL"
            await db.commit()
            await db.refresh(backup)

        except Exception as e:
            # Mark backup as failed and remove partial zip file
            if os.path.exists(filepath_temp):
                try:
                    os.remove(filepath_temp)
                except Exception:
                    pass
            backup.status = "FAILED"
            await db.commit()
            await db.refresh(backup)
            raise e
            
        finally:
            if is_running:
                # Re-enable active writing to files
                await process_manager.write_stdin("save-on")

        return backup

    async def restore_backup(self, db: AsyncSession, backup: Backup) -> None:
        if not os.path.exists(backup.filepath):
            raise FileNotFoundError(f"Backup file not found on disk: {backup.filepath}")

        # Check if the server was running/starting
        was_running = process_manager.status in ("RUNNING", "STARTING")

        if was_running:
            # Trigger shutdown and wait until stopped
            await process_manager.stop()
            # Give ports/threads a moment to clear
            await asyncio.sleep(2)

        try:
            # Purge current files except critical folders/jar in worker thread
            await asyncio.to_thread(
                purge_server_directory,
                settings.MINECRAFT_SERVER_DIR,
                settings.MINECRAFT_JAR_NAME
            )

            # Extract backup contents
            await asyncio.to_thread(
                extract_zip_file,
                backup.filepath,
                settings.MINECRAFT_SERVER_DIR
            )

        except Exception as e:
            # If restoration crashed midway, server might be in a broken state. Log it
            print(f"[Backup Restoration Error]: {str(e)}")
            raise e

        finally:
            # Re-spawn server if it was running previously
            if was_running:
                await process_manager.start()

    async def delete_backup(self, db: AsyncSession, backup: Backup) -> None:
        if os.path.exists(backup.filepath):
            try:
                os.remove(backup.filepath)
            except Exception as e:
                # Still proceed to delete from DB but warning is logged
                print(f"[Backup File Deletion Error]: {str(e)}")
        
        await BackupRepository.delete(db, backup)

backup_service = BackupService()
