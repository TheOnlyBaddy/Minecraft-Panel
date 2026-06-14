import os
import zipfile
import shutil
import tempfile
import pytest
from fastapi import status
from httpx import AsyncClient


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

def create_mock_jar(jar_path: str, plugin_yml_content: str):
    os.makedirs(os.path.dirname(jar_path), exist_ok=True)
    with zipfile.ZipFile(jar_path, 'w') as jar:
        jar.writestr("plugin.yml", plugin_yml_content)

@pytest.mark.asyncio
async def test_plugin_endpoints(client: AsyncClient, temp_server_dir):
    client = await get_admin_client(client)
    
    # Define test directories
    plugins_dir = os.path.join(temp_server_dir, "plugins")
    os.makedirs(plugins_dir, exist_ok=True)
    
    # 1. Test GET /api/server/plugins (Empty initially)
    resp = await client.get("/api/server/plugins")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == []
    
    # Create a mock plugin jar file
    plugin_yml = """
name: TestPlugin
version: 1.0.0
description: A mock testing plugin
authors: [Zen, Alex]
website: testplugin.com
"""
    jar_file_path = os.path.join(plugins_dir, "TestPlugin-1.0.0.jar")
    create_mock_jar(jar_file_path, plugin_yml)
    
    # 2. Test GET /api/server/plugins (Should return TestPlugin)
    resp = await client.get("/api/server/plugins")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "TestPlugin"
    assert data[0]["version"] == "1.0.0"
    assert data[0]["authors"] == ["Zen", "Alex"]
    assert data[0]["website"] == "testplugin.com"
    assert data[0]["file_name"] == "TestPlugin-1.0.0.jar"

    # 3. Test DELETE /api/server/plugins (Uninstall)
    testplugin_config_dir = os.path.join(plugins_dir, "TestPlugin-1.0.0")
    os.makedirs(testplugin_config_dir, exist_ok=True)
    assert os.path.exists(testplugin_config_dir)

    resp = await client.delete("/api/server/plugins?file_name=TestPlugin-1.0.0.jar")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["status"] == "success"

    # Verify both the jar file and the config directory are deleted
    assert not os.path.exists(jar_file_path)
    assert not os.path.exists(testplugin_config_dir)

    # 4. Test POST /api/server/plugins/upload
    upload_file_content = b"fake uploaded plugin jar content"
    files = {"file": ("UploadedPlugin.jar", upload_file_content, "application/java-archive")}
    resp = await client.post("/api/server/plugins/upload", files=files)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["status"] == "success"
    
    uploaded_jar_path = os.path.join(plugins_dir, "UploadedPlugin.jar")
    assert os.path.exists(uploaded_jar_path)
    with open(uploaded_jar_path, "rb") as f:
        assert f.read() == upload_file_content
