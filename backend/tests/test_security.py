import json
import pytest
from fastapi import status
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.services.process_manager import process_manager
from app.api.deps import login_limiter

@pytest.mark.asyncio
async def test_security_headers_on_health_check(client: AsyncClient):
    # Retrieve health endpoint
    resp = await client.get("/api/health")
    assert resp.status_code == status.HTTP_200_OK
    
    # Assert presence of security headers
    headers = resp.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert "Strict-Transport-Security" in headers
    assert "max-age=31536000" in headers["Strict-Transport-Security"]
    assert "Content-Security-Policy" in headers

@pytest.mark.asyncio
async def test_cors_origin_whitelisting(client: AsyncClient):
    # Test unauthorized origin
    resp = await client.get("/api/health", headers={"Origin": "http://unauthorized-hackers.com"})
    assert resp.headers.get("access-control-allow-origin") != "http://unauthorized-hackers.com"

    # Test authorized origin (from settings defaults)
    resp = await client.get("/api/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })
    # Since health has CORS applied via main, it should return access-control-allow-origin
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"

@pytest.mark.asyncio
async def test_login_rate_limiting(client: AsyncClient):
    # Reset the limiter state before testing to ensure fresh start
    login_limiter.history.clear()

    # Trigger 5 login attempts (incorrect password triggers 400 but executes the dependency)
    for _ in range(5):
        resp = await client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "wrongpassword"}
        )
        # Verify it went through to login logic (status 400, not 429)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    # The 6th attempt must be rate-limited
    limit_resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "wrongpassword"}
    )
    assert limit_resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many requests" in limit_resp.json()["detail"]

    # Cleanup state
    login_limiter.history.clear()

@pytest.mark.asyncio
async def test_console_command_whitelist_sanitization(client: AsyncClient, db):
    # Setup - seed DB and login as Admin
    await client.post("/api/auth/seed")
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert login_resp.status_code == status.HTTP_200_OK
    admin_token = login_resp.cookies["access_token"]
    client.cookies.set("access_token", admin_token)

    # 1. Valid Whitelisted commands should pass
    valid_commands = [
        "say hello",
        "op player-1",
        "ban user_name",
        "whitelist add player:2",
        "kick test?",
        "say caution!"
    ]
    for cmd in valid_commands:
        with patch.object(process_manager, "write_stdin", new_callable=AsyncMock) as mock_write:
            resp = await client.post(
                "/api/server/console/command",
                json={"command": cmd}
            )
            assert resp.status_code == status.HTTP_200_OK
            mock_write.assert_called_once_with(cmd)

    # 2. Invalid command symbols should be rejected
    invalid_commands = [
        "say hello; op admin", # semicolon command injection
        "say hello && echo hacked", # shell command execution
        "op admin &",
        "say hello | grep flag",
        "say hello $VAR",
        "say hello @a", # selector (if @ is not allowed)
        "say hello \"world\"", # quotes
        "say hello [test]" # brackets
    ]
    for cmd in invalid_commands:
        resp = await client.post(
            "/api/server/console/command",
            json={"command": cmd}
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "contains forbidden characters" in resp.json()["detail"]

    # 3. Truncation test: commands > 256 characters should be sliced
    long_but_valid_cmd = "say " + ("a" * 300)
    expected_truncated_cmd = "say " + ("a" * 252) # totals 256 characters
    
    with patch.object(process_manager, "write_stdin", new_callable=AsyncMock) as mock_write:
        resp = await client.post(
            "/api/server/console/command",
            json={"command": long_but_valid_cmd}
        )
        assert resp.status_code == status.HTTP_200_OK
        mock_write.assert_called_once_with(expected_truncated_cmd)
