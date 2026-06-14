import os
import shutil
import zipfile
import tempfile
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTasks
from app.config import settings
from app.api.deps import require_admin
from app.services.config_service import config_service
from app.services.process_manager import process_manager
from app.models.user import User

router = APIRouter(prefix="/server/worlds", tags=["worlds"])

def get_dir_size(path: str) -> int:
    total_size = 0
    if not os.path.exists(path):
        return 0
    if os.path.isfile(path):
        return os.path.getsize(path)
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def zip_directory(dir_path: str, zip_path: str):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(dir_path))
                zipf.write(file_path, arcname)

def cleanup_file(filepath: str):
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception:
            pass

@router.get("/stats")
async def get_world_stats(current_user: User = Depends(require_admin)):
    try:
        config = await config_service.get_config()
        level_name = config.get("level-name", "world")
        
        server_dir = os.path.abspath(settings.MINECRAFT_SERVER_DIR)
        world_path = os.path.join(server_dir, level_name)
        nether_path = os.path.join(server_dir, f"{level_name}_nether")
        end_path = os.path.join(server_dir, f"{level_name}_the_end")

        world_size = get_dir_size(world_path)
        nether_size = get_dir_size(nether_path)
        end_size = get_dir_size(end_path)
        
        total_size = world_size + nether_size + end_size

        return {
            "level_name": level_name,
            "exists": os.path.exists(world_path),
            "world_size": world_size,
            "nether_size": nether_size,
            "end_size": end_size,
            "total_size": total_size
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read world statistics: {str(e)}"
        )

@router.get("/download")
async def download_world(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin)
):
    try:
        config = await config_service.get_config()
        level_name = config.get("level-name", "world")
        
        server_dir = os.path.abspath(settings.MINECRAFT_SERVER_DIR)
        world_path = os.path.join(server_dir, level_name)

        if not os.path.exists(world_path):
            raise HTTPException(status_code=404, detail=f"World folder '{level_name}' not found.")

        # Create temporary zip file
        temp_dir = tempfile.gettempdir()
        zip_filename = f"world_{level_name}.zip"
        zip_filepath = os.path.join(temp_dir, zip_filename)

        # Zip world directory
        zip_directory(world_path, zip_filepath)

        # Enqueue cleanup task to delete temporary file after sending
        background_tasks.add_task(cleanup_file, zip_filepath)

        return FileResponse(
            path=zip_filepath,
            filename=zip_filename,
            media_type="application/zip"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to zip world folder: {str(e)}"
        )

@router.post("/reset")
async def reset_world(current_user: User = Depends(require_admin)):
    try:
        config = await config_service.get_config()
        level_name = config.get("level-name", "world")
        
        server_dir = os.path.abspath(settings.MINECRAFT_SERVER_DIR)
        world_path = os.path.join(server_dir, level_name)
        nether_path = os.path.join(server_dir, f"{level_name}_nether")
        end_path = os.path.join(server_dir, f"{level_name}_the_end")

        was_running = process_manager.status in ("STARTING", "RUNNING")

        # 1. Stop server if active
        if was_running:
            process_manager._append_log("[Panel]: Initiating server shutdown for world reset...")
            await process_manager.stop()
            import asyncio
            await asyncio.sleep(2)

        # 2. Delete world directories
        deleted_paths = []
        for path in (world_path, nether_path, end_path):
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                deleted_paths.append(os.path.basename(path))

        # 3. Start server again
        if was_running:
            process_manager._append_log("[Panel]: Worlds purged. Booting server to generate fresh worlds...")
            await process_manager.start()
        else:
            process_manager._append_log("[Panel]: Worlds purged. A fresh world will be generated on next start.")

        return {
            "status": "success", 
            "detail": f"Worlds successfully reset.",
            "deleted": deleted_paths
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset worlds: {str(e)}"
        )
