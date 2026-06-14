import os
import tempfile
import zipfile
import shutil
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.config import settings
from app.db.session import get_db
from app.services.process_manager import process_manager
from app.services.backup_service import backup_service
from app.repositories.backup_repo import BackupRepository
from app.models.backup import Backup
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_backup_and_restore_workflow(db):
    # Setup temporary directory for server files
    temp_server_dir = tempfile.mkdtemp()
    
    # Save original settings
    original_server_dir = settings.MINECRAFT_SERVER_DIR
    settings.MINECRAFT_SERVER_DIR = temp_server_dir
    
    # Create dummy server files
    os.makedirs(os.path.join(temp_server_dir, "world", "region"), exist_ok=True)
    os.makedirs(os.path.join(temp_server_dir, "logs"), exist_ok=True)
    os.makedirs(os.path.join(temp_server_dir, "cache"), exist_ok=True)

    with open(os.path.join(temp_server_dir, "paper.jar"), "w") as f:
        f.write("mock-jar-content")
    with open(os.path.join(temp_server_dir, "server.properties"), "w") as f:
        f.write("max-players=20")
    with open(os.path.join(temp_server_dir, "world", "level.dat"), "w") as f:
        f.write("mock-world-content")
    with open(os.path.join(temp_server_dir, "logs", "latest.log"), "w") as f:
        f.write("mock-log-content")
    with open(os.path.join(temp_server_dir, "cache", "cache.json"), "w") as f:
        f.write("mock-cache-content")

    # Override database session for dependency injection
    async def override_get_db():
        try:
            yield db
        finally:
            await db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Clean starting status
    process_manager.status = "RUNNING"

    try:
        # Patch process manager write_stdin & stop & start
        with patch.object(process_manager, "write_stdin", new_callable=AsyncMock) as mock_write, \
             patch.object(process_manager, "stop", new_callable=AsyncMock) as mock_stop, \
             patch.object(process_manager, "start", new_callable=AsyncMock) as mock_start:
            
            # 1. Create backup
            backup = await backup_service.create_backup(db, user_id=None)
            
            # Assert save-off and save-all are sent to standard input
            mock_write.assert_any_call("save-off")
            mock_write.assert_any_call("save-all")
            mock_write.assert_any_call("save-on")
            
            # Assert file properties
            assert backup.status == "SUCCESSFUL"
            assert os.path.exists(backup.filepath)
            assert backup.file_size > 0
            
            # Verify zip content exclusions
            with zipfile.ZipFile(backup.filepath, "r") as zipf:
                namelist = zipf.namelist()
                assert "server.properties" in namelist
                assert "world/level.dat" in namelist
                assert "paper.jar" not in namelist
                assert "logs/latest.log" not in namelist
                assert "cache/cache.json" not in namelist

            # Modify local files to test restore purging
            with open(os.path.join(temp_server_dir, "server.properties"), "w") as f:
                f.write("max-players=100") # changed
            with open(os.path.join(temp_server_dir, "world", "level.dat"), "w") as f:
                f.write("corrupt-world") # changed
            # Add an orphan file
            with open(os.path.join(temp_server_dir, "world", "orphan.txt"), "w") as f:
                f.write("orphan")

            # 2. Restore backup
            await backup_service.restore_backup(db, backup)
            
            # Assert server was stopped and restarted
            mock_stop.assert_called_once()
            mock_start.assert_called_once()

            # Verify files are rolled back and orphan is purged
            with open(os.path.join(temp_server_dir, "server.properties"), "r") as f:
                assert f.read() == "max-players=20"
            with open(os.path.join(temp_server_dir, "world", "level.dat"), "r") as f:
                assert f.read() == "mock-world-content"
            assert not os.path.exists(os.path.join(temp_server_dir, "world", "orphan.txt"))

            # Preserved files should remain
            assert os.path.exists(os.path.join(temp_server_dir, "paper.jar"))
            assert os.path.exists(os.path.join(temp_server_dir, "logs", "latest.log"))
            assert os.path.exists(os.path.join(temp_server_dir, "cache", "cache.json"))

            # 3. Delete backup
            filepath = backup.filepath
            await backup_service.delete_backup(db, backup)
            assert not os.path.exists(filepath)
            
            # Assert database record deleted
            res = await db.execute(select(Backup).where(Backup.id == backup.id))
            assert res.scalars().first() is None

    finally:
        fastapi_app.dependency_overrides.clear()
        settings.MINECRAFT_SERVER_DIR = original_server_dir
        shutil.rmtree(temp_server_dir)

@pytest.mark.asyncio
async def test_backup_api_rbac_restrictions(db):
    async def override_get_db():
        try:
            yield db
        finally:
            await db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Create admin and non-admin users manually for testing RBAC
    from app.core.security import get_password_hash
    from app.repositories.user_repo import UserRepository
    admin_hash = get_password_hash("adminpassword")
    await UserRepository.create(
        db,
        username="admin",
        email="admin@example.com",
        password_hash=admin_hash,
        role="ROLE_ADMIN"
    )
    user_hash = get_password_hash("userpassword")
    await UserRepository.create(
        db,
        username="test_user",
        email="test_user@example.com",
        password_hash=user_hash,
        role="ROLE_USER"
    )
    await db.commit()

    # We run RBAC endpoint checks using TestClient synchronously inside thread
    def run_rbac_tests():
        test_client = TestClient(fastapi_app)
        
        # Login Non-admin
        user_login = test_client.post("/api/auth/login", data={"username": "test_user", "password": "userpassword"})
        user_token = user_login.cookies.get("access_token")
        
        # Login Admin
        admin_login = test_client.post("/api/auth/login", data={"username": "admin", "password": "adminpassword"})
        admin_token = admin_login.cookies.get("access_token")

        # 1. Non-admin attempts should be forbidden
        test_client.cookies.set("access_token", user_token)
        
        create_res = test_client.post("/api/backups")
        assert create_res.status_code == 403
        
        restore_res = test_client.post("/api/backups/1/restore")
        assert restore_res.status_code == 403
        
        delete_res = test_client.delete("/api/backups/1")
        assert delete_res.status_code == 403

        # Non-admin cannot list backups
        list_res = test_client.get("/api/backups")
        assert list_res.status_code == 403

        # 2. Admin attempts should be allowed
        test_client.cookies.set("access_token", admin_token)
        
        # Triggering a backup via mock setup to prevent real zipping
        with patch.object(backup_service, "create_backup", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Backup(id=1, filename="b.zip", filepath="b.zip", file_size=1, checksum="c", status="SUCCESSFUL")
            res = test_client.post("/api/backups")
            assert res.status_code == 200
            mock_create.assert_called_once()

    try:
        await asyncio.to_thread(run_rbac_tests)
    finally:
        fastapi_app.dependency_overrides.clear()
