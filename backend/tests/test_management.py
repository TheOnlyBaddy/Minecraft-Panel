import os
import json
import shutil
import tempfile
import pytest
from fastapi import status
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.config import settings
from app.services.config_service import config_service

@pytest.fixture
def temp_server_dir():
    temp_dir = tempfile.mkdtemp()
    original_server_dir = settings.MINECRAFT_SERVER_DIR
    settings.MINECRAFT_SERVER_DIR = temp_dir
    yield temp_dir
    settings.MINECRAFT_SERVER_DIR = original_server_dir
    shutil.rmtree(temp_dir)

async def get_admin_client(client: AsyncClient):
    await client.post("/api/auth/seed")
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert login_resp.status_code == status.HTTP_200_OK
    admin_token = login_resp.cookies["access_token"]
    client.cookies.set("access_token", admin_token)
    return client

# ==================== 1. Users API Tests ====================

@pytest.mark.asyncio
async def test_users_crud_operations(client: AsyncClient):
    client = await get_admin_client(client)

    # List users (only admin exists initially)
    resp = await client.get("/api/users")
    assert resp.status_code == status.HTTP_200_OK
    users = resp.json()
    assert len(users) == 1
    assert users[0]["username"] == "admin"
    admin_user_id = users[0]["id"]

    # Create new user
    resp = await client.post(
        "/api/users",
        json={"username": "moderator", "email": "moderator@example.com", "password": "modpassword"}
    )
    assert resp.status_code == status.HTTP_200_OK
    new_user = resp.json()
    assert new_user["username"] == "moderator"
    assert new_user["email"] == "moderator@example.com"
    mod_user_id = new_user["id"]

    # Check list has 2 users
    resp = await client.get("/api/users")
    assert len(resp.json()) == 2

    # Create duplicate user (must fail)
    resp = await client.post(
        "/api/users",
        json={"username": "moderator", "email": "different@example.com", "password": "otherpassword"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already registered" in resp.json()["detail"]

    # Create duplicate email (must fail)
    resp = await client.post(
        "/api/users",
        json={"username": "different_mod", "email": "moderator@example.com", "password": "otherpassword"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in resp.json()["detail"]

    # Create empty username (must fail)
    resp = await client.post(
        "/api/users",
        json={"username": "   ", "email": "test_empty@example.com", "password": "somepassword"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

    # Login as the new non-admin/other user to verify they cannot manage users
    # Logout admin
    await client.post("/api/auth/logout")
    client.cookies.delete("access_token")

    # Login as moderator (who is not "admin")
    resp_login = await client.post(
        "/api/auth/login",
        data={"username": "moderator", "password": "modpassword"}
    )
    assert resp_login.status_code == status.HTTP_200_OK
    mod_token = resp_login.cookies["access_token"]
    client.cookies.set("access_token", mod_token)

    # Attempt to create a user as moderator (must fail with 403)
    resp = await client.post(
        "/api/users",
        json={"username": "user3", "email": "user3@example.com", "password": "somepassword"}
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "Only the primary 'admin' account is authorized" in resp.json()["detail"]

    # Attempt to delete a user as moderator (must fail with 403)
    resp = await client.delete(f"/api/users/{admin_user_id}")
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "Only the primary 'admin' account is authorized" in resp.json()["detail"]

    # Switch back to admin to clean up/continue
    await client.post("/api/auth/logout")
    client.cookies.delete("access_token")

    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert login_resp.status_code == status.HTTP_200_OK
    admin_token = login_resp.cookies["access_token"]
    client.cookies.set("access_token", admin_token)

    # Attempt to delete own user account (must fail)
    resp = await client.delete(f"/api/users/{admin_user_id}")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot delete your own active administrator account" in resp.json()["detail"]

    # Delete other user (must succeed)
    resp = await client.delete(f"/api/users/{mod_user_id}")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["status"] == "success"

    # Verify deleted user is gone
    resp = await client.get("/api/users")
    assert len(resp.json()) == 1

# ==================== 2. Players List API Tests ====================

@pytest.mark.asyncio
async def test_players_list_management(client: AsyncClient, temp_server_dir):
    client = await get_admin_client(client)

    # Get empty whitelist
    resp = await client.get("/api/server/players?list_type=whitelist")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == []

    # Add player to whitelist (Mocking resolve_uuid)
    with patch("app.api.players.resolve_uuid", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = "069a79f4-44e9-4726-a5be-fca90e38aaf5"
        resp = await client.post(
            "/api/server/players/add",
            json={"list_type": "whitelist", "username_or_ip": "Notch"}
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["status"] == "success"

        # Verify player in whitelist
        resp = await client.get("/api/server/players?list_type=whitelist")
        players = resp.json()
        assert len(players) == 1
        assert players[0]["name"] == "Notch"
        assert players[0]["uuid"] == "069a79f4-44e9-4726-a5be-fca90e38aaf5"

        # Try adding again (idempotent success or already added message)
        resp = await client.post(
            "/api/server/players/add",
            json={"list_type": "whitelist", "username_or_ip": "Notch"}
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "already in the list" in resp.json()["detail"]

        # Remove player from whitelist
        resp = await client.post(
            "/api/server/players/remove",
            json={"list_type": "whitelist", "username_or_ip": "Notch"}
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["status"] == "success"

    # Verify whitelist is empty again
    resp = await client.get("/api/server/players?list_type=whitelist")
    assert resp.json() == []

    # Test banned-ips list
    resp = await client.post(
        "/api/server/players/add",
        json={"list_type": "banned-ips", "username_or_ip": "192.168.1.1", "reason": "Spamming"}
    )
    assert resp.status_code == status.HTTP_200_OK
    
    resp = await client.get("/api/server/players?list_type=banned-ips")
    banned_ips = resp.json()
    assert len(banned_ips) == 1
    assert banned_ips[0]["ip"] == "192.168.1.1"
    assert banned_ips[0]["reason"] == "Spamming"

    # Remove IP
    resp = await client.post(
        "/api/server/players/remove",
        json={"list_type": "banned-ips", "username_or_ip": "192.168.1.1"}
    )
    assert resp.status_code == status.HTTP_200_OK
    
    # Try removing non-existent (fails 404)
    resp = await client.post(
        "/api/server/players/remove",
        json={"list_type": "banned-ips", "username_or_ip": "192.168.1.1"}
    )
    assert resp.status_code == status.HTTP_404_NOT_FOUND

    # Test GET /api/server/players/online
    from app.services.process_manager import process_manager
    process_manager.active_players_set = {"Steve", "\x1B [38;2;255;255;85mBaddyyyy"}
    try:
        resp = await client.get("/api/server/players/online")
        assert resp.status_code == status.HTTP_200_OK
        online_players = resp.json()
        assert len(online_players) == 2
        names = {p["name"] for p in online_players}
        assert names == {"Steve", "Baddyyyy"}
        assert "uuid" in online_players[0]
    finally:
        process_manager.active_players_set = set()

# ==================== 3. Files API Tests ====================

@pytest.mark.asyncio
async def test_files_explorer_operations(client: AsyncClient, temp_server_dir):
    client = await get_admin_client(client)

    # 1. Write file
    resp = await client.post(
        "/api/server/files/write",
        json={"path": "server.properties", "content": "difficulty=hard\npvp=true"}
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["status"] == "success"

    # 2. List directory
    resp = await client.get("/api/server/files/list?path=")
    assert resp.status_code == status.HTTP_200_OK
    files = resp.json()
    assert len(files) == 1
    assert files[0]["name"] == "server.properties"
    assert files[0]["isDir"] is False
    assert files[0]["isEditable"] is True

    # 3. Read file content
    resp = await client.get("/api/server/files/read?path=server.properties")
    assert resp.status_code == status.HTTP_200_OK
    assert "difficulty=hard" in resp.json()["content"]

    # 4. Path traversal attempt on read
    resp = await client.get("/api/server/files/read?path=../../etc/passwd")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "Path traversal attempt detected" in resp.json()["detail"]

    # 5. Path traversal attempt on write
    resp = await client.post(
        "/api/server/files/write",
        json={"path": "../hacked.txt", "content": "hacked"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

    # 6. Guard: Block writing/saving binary extensions or unsafe types
    resp = await client.post(
        "/api/server/files/write",
        json={"path": "virus.exe", "content": "binarystuff"}
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST

    # 7. Guard: Block writing to/overwriting paper.jar
    resp = await client.post(
        "/api/server/files/write",
        json={"path": "paper.jar", "content": "fake jar content"}
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "Modifying the main server JAR file is forbidden" in resp.json()["detail"]

    # 8. Guard: Block deleting paper.jar
    # Create a dummy paper.jar on disk
    paper_path = os.path.join(temp_server_dir, "paper.jar")
    with open(paper_path, "w") as f:
        f.write("jar contents")
        
    resp = await client.delete("/api/server/files/delete?path=paper.jar")
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "Deleting the main server JAR file is forbidden" in resp.json()["detail"]

    # 9. Guard: Block deleting the server root directory
    resp = await client.delete("/api/server/files/delete?path=")
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "Deleting the main server directory is forbidden" in resp.json()["detail"]

    # 10. Valid file delete
    resp = await client.delete("/api/server/files/delete?path=server.properties")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["status"] == "success"

# ==================== 4. Worlds API Tests ====================

@pytest.mark.asyncio
async def test_worlds_management(client: AsyncClient, temp_server_dir):
    client = await get_admin_client(client)

    # Setup mock properties to define world name
    properties_path = os.path.join(temp_server_dir, "server.properties")
    with open(properties_path, "w") as f:
        f.write("level-name=my_world\n")

    # Create mock world directories
    world_dir = os.path.join(temp_server_dir, "my_world")
    os.makedirs(world_dir, exist_ok=True)
    with open(os.path.join(world_dir, "level.dat"), "w") as f:
        f.write("mock level data")

    # 1. GET /stats
    resp = await client.get("/api/server/worlds/stats")
    assert resp.status_code == status.HTTP_200_OK
    stats = resp.json()
    assert stats["level_name"] == "my_world"
    assert stats["exists"] is True
    assert stats["total_size"] > 0

    # 2. GET /download
    resp = await client.get("/api/server/worlds/download")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.headers["content-type"] == "application/zip"
    assert "attachment" in resp.headers["content-disposition"]
    assert "world_my_world.zip" in resp.headers["content-disposition"]

    # 3. POST /reset
    with patch("app.services.process_manager.process_manager.start", new_callable=AsyncMock) as mock_start, \
         patch("app.services.process_manager.process_manager.stop", new_callable=AsyncMock) as mock_stop:
        
        # Test reset when server status is RUNNING
        from app.services.process_manager import process_manager
        process_manager.status = "RUNNING"
        
        resp = await client.post("/api/server/worlds/reset")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["status"] == "success"
        
        # Check that stop was called, directory deleted, and start was called again
        mock_stop.assert_called_once()
        mock_start.assert_called_once()
        assert not os.path.exists(world_dir)


