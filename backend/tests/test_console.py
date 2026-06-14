import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.db.session import get_db
from app.services.process_manager import process_manager
from app.services.console_service import console_service
from app.models.audit_log import AuditLog
from tests.conftest import TestingSessionLocal
from sqlalchemy.future import select

@pytest.mark.asyncio
async def test_console_websocket_and_command_auditing(db):
    # Override get_db dependency to point to our test database session
    async def override_get_db():
        try:
            yield db
        finally:
            await db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Seed the console log buffer with dummy logs
    process_manager.log_buffer = ["Log line 1", "Log line 2"]

    main_loop = asyncio.get_running_loop()

    def run_console_tests():
        test_client = TestClient(fastapi_app)

        # 1. WebSocket connection without token cookie should fail
        with pytest.raises(Exception):
            with test_client.websocket_connect("/api/server/console"):
                pass

        # 2. Seed database & login as admin
        seed_res = test_client.post("/api/auth/seed")
        assert seed_res.status_code == 200
        
        login_res = test_client.post("/api/auth/login", data={"username": "admin", "password": "adminpassword"})
        assert login_res.status_code == 200
        token = login_res.cookies.get("access_token")
        assert token is not None

        # Set session cookie in client
        test_client.cookies.set("access_token", token)

        # 3. Connect to console WebSocket
        with test_client.websocket_connect("/api/server/console") as websocket:
            # First message received must be the log history batch
            history_data = websocket.receive_json()
            assert history_data["type"] == "history"
            assert history_data["lines"] == ["Log line 1", "Log line 2"]

            # 4. Command Input Validation checks (Newlines/Carriage Returns)
            bad_cmd_res = test_client.post(
                "/api/server/console/command",
                json={"command": "say hello\nop admin"}
            )
            assert bad_cmd_res.status_code == 400
            assert "Newline or carriage return" in bad_cmd_res.json()["detail"]

            # 5. Command Execution (Valid Command)
            # Patch write_stdin to prevent writing to a non-existent subprocess
            with patch.object(process_manager, "write_stdin", new_callable=AsyncMock) as mock_write:
                cmd_res = test_client.post(
                    "/api/server/console/command",
                    json={"command": "say panel test"}
                )
                assert cmd_res.status_code == 200
                mock_write.assert_called_once_with("say panel test")

            # 6. Stream real-time logs over WebSocket
            # We schedule _append_log to execute on the main event loop threadsafe
            main_loop.call_soon_threadsafe(process_manager._append_log, "Server thread/INFO: User Alex joined the game")
            
            # Read streaming message
            stream_data = websocket.receive_json()
            assert stream_data["type"] == "log"
            assert "User Alex joined the game" in stream_data["line"]

    try:
        # Run tests in separate thread so synchronous TestClient WS reads do not block main event loop
        await asyncio.to_thread(run_console_tests)

        # Verify command execution recorded in audit logs table
        result = await db.execute(select(AuditLog).where(AuditLog.action == "EXECUTE_COMMAND"))
        audit_record = result.scalars().first()
        assert audit_record is not None
        assert audit_record.target == "server"
        details = json.loads(audit_record.details_json)
        assert details["command"] == "say panel test"

    finally:
        fastapi_app.dependency_overrides.clear()
        console_service.active_connections.clear()
