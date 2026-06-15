import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi import status
from app.services.process_manager import process_manager
from app.models.server_event import ServerEvent
from sqlalchemy.future import select
from tests.conftest import TestingSessionLocal

# Mock structures for StreamReader
class MockStreamReader:
    def __init__(self, lines):
        processed_lines = []
        for line in lines:
            if isinstance(line, str):
                line_bytes = line.encode("utf-8")
            else:
                line_bytes = line
            
            # Ensure it ends with newline unless it contains pause prompts
            if not line_bytes.endswith(b"\n") and not line_bytes.endswith(b"\r") and b"Press any key to continue" not in line_bytes:
                line_bytes += b"\n"
            processed_lines.append(line_bytes)
            
        self.data = b"".join(processed_lines)
        self.index = 0

    async def read(self, n):
        if self.index >= len(self.data):
            return b""
        chunk = self.data[self.index:self.index + n]
        self.index += len(chunk)
        await asyncio.sleep(0.001)
        return chunk

    async def readline(self):
        if self.index >= len(self.data):
            return b""
        newline_pos = self.data.find(b"\n", self.index)
        if newline_pos == -1:
            chunk = self.data[self.index:]
        else:
            chunk = self.data[self.index:newline_pos + 1]
        self.index += len(chunk)
        await asyncio.sleep(0.001)
        return chunk

# Mock structures for StreamWriter
class MockStreamWriter:
    def __init__(self):
        self.write_history = []

    def write(self, data):
        self.write_history.append(data.decode("utf-8"))

    async def drain(self):
        await asyncio.sleep(0.01)

# Mock process container
class MockProcess:
    def __init__(self, stdout_lines, stderr_lines, exit_code=0, delay=0.1):
        self.stdin = MockStreamWriter()
        self.stdout = MockStreamReader(stdout_lines)
        self.stderr = MockStreamReader(stderr_lines)
        self._exit_code = exit_code
        self.is_killed = False
        self.delay = delay

    async def wait(self):
        # Allow background readers time to read streams first
        await asyncio.sleep(self.delay)
        return self._exit_code

    def kill(self):
        self.is_killed = True
        self._exit_code = -9

@pytest_asyncio.fixture(autouse=True)
async def cleanup_process_manager():
    # Make sure we reset process manager status before and after each test
    process_manager.status = "STOPPED"
    process_manager.process = None
    process_manager.log_buffer.clear()
    process_manager.session_factory = TestingSessionLocal
    yield
    # Cleanup task loops if any running
    if process_manager.process:
        await process_manager.kill()
    process_manager.status = "STOPPED"
    process_manager.process = None
    process_manager.log_buffer.clear()
    process_manager.session_factory = None

@pytest.mark.asyncio
async def test_server_startup_success(client: AsyncClient, db):
    # 1. Seed database to authenticate admin
    await client.post("/api/auth/seed")
    login_res = await client.post("/api/auth/login", data={"username": "admin", "password": "adminpassword"})
    token = login_res.cookies["access_token"]
    client.cookies.set("access_token", token)

    mock_proc = MockProcess(
        stdout_lines=[
            "Starting minecraft server version 1.20.4",
            "Preparing level \"world\"",
            "[Server thread/INFO]: Done (10.5s)! For help, type \"help\"",
            "Alex joined the game"
        ],
        stderr_lines=[],
        delay=10.0
    )

    # Patch create_subprocess_exec to return our mock process
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_proc
        
        # Trigger startup endpoint
        res = await client.post("/api/server/lifecycle", json={"action": "start"})
        assert res.status_code == status.HTTP_200_OK, f"Response text: {res.text}"
        assert res.json()["state"] == "STARTING"
        
        # Wait for log readers to scan inputs and watcher to complete
        await asyncio.sleep(0.2)
        
        # Verify status transitioned to RUNNING upon matching "Done" log
        assert process_manager.status == "RUNNING"
        
        # Verify player was parsed and added to active players set
        assert "Alex" in process_manager.active_players_set

        # Verify server events logged to database
        result = await db.execute(select(ServerEvent).where(ServerEvent.event_type == "START"))
        start_event = result.scalars().first()
        assert start_event is not None
        assert "launched" in start_event.description

@pytest.mark.asyncio
async def test_server_stop_graceful(client: AsyncClient, db):
    # Authenticate admin
    await client.post("/api/auth/seed")
    login_res = await client.post("/api/auth/login", data={"username": "admin", "password": "adminpassword"})
    token = login_res.cookies["access_token"]
    client.cookies.set("access_token", token)

    mock_proc = MockProcess(
        stdout_lines=["Stopping server", "Saving worlds", "Closing Thread"],
        stderr_lines=[],
        exit_code=0
    )
    
    # Establish running process manager context
    process_manager.process = mock_proc
    process_manager.status = "RUNNING"
    process_manager._watcher_task = asyncio.create_task(process_manager._process_watcher())
    process_manager._log_readers = [
        asyncio.create_task(process_manager._read_stream(mock_proc.stdout, "stdout")),
        asyncio.create_task(process_manager._read_stream(mock_proc.stderr, "stderr"))
    ]

    # Trigger stop command
    res = await client.post("/api/server/lifecycle", json={"action": "stop"})
    assert res.status_code == status.HTTP_200_OK
    
    # Wait for process wait and stop tasks to execute
    await asyncio.sleep(0.2)
    
    # Verify process successfully exited and logged stop event
    assert process_manager.status == "STOPPED"
    assert "stop\n" in mock_proc.stdin.write_history
    
    result = await db.execute(select(ServerEvent).where(ServerEvent.event_type == "STOP"))
    stop_event = result.scalars().first()
    assert stop_event is not None
    assert stop_event.exit_code == 0

@pytest.mark.asyncio
async def test_server_crash_detection(client: AsyncClient, db):
    # Authenticate admin
    await client.post("/api/auth/seed")
    login_res = await client.post("/api/auth/login", data={"username": "admin", "password": "adminpassword"})
    token = login_res.cookies["access_token"]
    client.cookies.set("access_token", token)

    # Exit code 1 indicates unexpected exit (Crash)
    mock_proc = MockProcess(
        stdout_lines=["[Server thread/WARN]: Out of memory!"],
        stderr_lines=[],
        exit_code=1
    )

    process_manager.process = mock_proc
    process_manager.status = "RUNNING"
    process_manager._watcher_task = asyncio.create_task(process_manager._process_watcher())
    process_manager._log_readers = [
        asyncio.create_task(process_manager._read_stream(mock_proc.stdout, "stdout"))
    ]

    # Process wait completes (triggered automatically in background by the watcher)
    await asyncio.sleep(0.2)
    
    # Verify status changed to CRASHED
    assert process_manager.status == "CRASHED"
    
    # Verify server events logged the crash event with description
    result = await db.execute(select(ServerEvent).where(ServerEvent.event_type == "CRASH"))
    crash_event = result.scalars().first()
    assert crash_event is not None
    assert crash_event.exit_code == 1
    assert "terminated unexpectedly" in crash_event.description

@pytest.mark.asyncio
async def test_server_startup_with_start_bat(client: AsyncClient):
    await client.post("/api/auth/seed")
    login_res = await client.post("/api/auth/login", data={"username": "admin", "password": "adminpassword"})
    token = login_res.cookies["access_token"]
    client.cookies.set("access_token", token)

    mock_proc = MockProcess(
        stdout_lines=["[Server thread/INFO]: Done (10.5s)!"],
        stderr_lines=[]
    )

    def mock_exists_bat(path):
        if path.endswith("playit.exe") or path.endswith("playit"):
            return False
        return True

    with patch("app.services.process_manager.os.name", "nt"), \
         patch("app.services.process_manager.os.path.exists", side_effect=mock_exists_bat), \
         patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        
        mock_exec.return_value = mock_proc
        res = await client.post("/api/server/lifecycle", json={"action": "start"})
        assert res.status_code == status.HTTP_200_OK
        
        # Verify that start.bat was called on Windows
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args == ("cmd.exe", "/c", "start.bat")

@pytest.mark.asyncio
async def test_server_startup_with_start_sh(client: AsyncClient):
    await client.post("/api/auth/seed")
    login_res = await client.post("/api/auth/login", data={"username": "admin", "password": "adminpassword"})
    token = login_res.cookies["access_token"]
    client.cookies.set("access_token", token)

    mock_proc = MockProcess(
        stdout_lines=["[Server thread/INFO]: Done (10.5s)!"],
        stderr_lines=[]
    )

    def mock_exists_sh(path):
        if path.endswith("playit.exe") or path.endswith("playit"):
            return False
        return True

    with patch("app.services.process_manager.os.name", "posix"), \
         patch("app.services.process_manager.os.path.exists", side_effect=mock_exists_sh), \
         patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        
        mock_exec.return_value = mock_proc
        res = await client.post("/api/server/lifecycle", json={"action": "start"})
        assert res.status_code == status.HTTP_200_OK
        
        # Verify that start.sh was called on Unix
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args == ("/bin/sh", "start.sh")

@pytest.mark.asyncio
async def test_server_startup_fallback_java(client: AsyncClient):
    await client.post("/api/auth/seed")
    login_res = await client.post("/api/auth/login", data={"username": "admin", "password": "adminpassword"})
    token = login_res.cookies["access_token"]
    client.cookies.set("access_token", token)

    mock_proc = MockProcess(
        stdout_lines=["[Server thread/INFO]: Done (10.5s)!"],
        stderr_lines=[]
    )

    import os
    def mock_exists_java(path):
        if path.endswith("start.bat") or path.endswith("start.sh") or path.endswith("playit.exe") or path.endswith("playit"):
            return False
        return True

    with patch("app.services.process_manager.os.name", "nt"), \
         patch("app.services.process_manager.os.path.exists", side_effect=mock_exists_java), \
         patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        
        mock_exec.return_value = mock_proc
        res = await client.post("/api/server/lifecycle", json={"action": "start"})
        assert res.status_code == status.HTTP_200_OK
        
        # Verify that fallback java command was called
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert args[0] == "java"
        assert "-jar" in args

@pytest.mark.asyncio
async def test_server_pause_bypass(client: AsyncClient):
    await client.post("/api/auth/seed")
    login_res = await client.post("/api/auth/login", data={"username": "admin", "password": "adminpassword"})
    token = login_res.cookies["access_token"]
    client.cookies.set("access_token", token)

    # The stream outputs a pause statement without a newline
    mock_proc = MockProcess(
        stdout_lines=["Press any key to continue . . ."],
        stderr_lines=[],
        exit_code=0
    )

    process_manager.process = mock_proc
    process_manager.status = "RUNNING"
    process_manager._watcher_task = asyncio.create_task(process_manager._process_watcher())
    process_manager._log_readers = [
        asyncio.create_task(process_manager._read_stream(mock_proc.stdout, "stdout"))
    ]

    # Wait for the stream to read and trigger bypass
    await asyncio.sleep(0.1)

    # Check that a newline was written to stdin to satisfy the pause prompt
    assert "\n" in mock_proc.stdin.write_history
