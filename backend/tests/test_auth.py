import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy", "service": "Antigravity Panel"}

@pytest.mark.asyncio
async def test_auth_workflow(client: AsyncClient):
    # 1. Seed database
    response = await client.post("/api/auth/seed")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "success"
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["username"] == "admin"
    assert data["accounts"][0]["password"] == "adminpassword"

    # 2. Seed again should fail
    response_retry = await client.post("/api/auth/seed")
    assert response_retry.status_code == status.HTTP_400_BAD_REQUEST
    assert "already been seeded" in response_retry.json()["detail"]

    # 3. Access /me without cookie should fail
    response_me_fail = await client.get("/api/auth/me")
    assert response_me_fail.status_code == status.HTTP_401_UNAUTHORIZED

    # 4. Login with incorrect password should fail
    response_login_fail = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "wrongpassword"}
    )
    assert response_login_fail.status_code == status.HTTP_400_BAD_REQUEST

    # 5. Login with correct password (username) should succeed
    response_login = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert response_login.status_code == status.HTTP_200_OK
    login_data = response_login.json()
    assert login_data["username"] == "admin"
    assert login_data["role"] == "ROLE_ADMIN"
    
    # Verify cookie was set
    assert "access_token" in response_login.cookies
    token = response_login.cookies["access_token"]
    assert token is not None

    # 5b. Login with correct password (email) should succeed
    await client.post("/api/auth/logout")
    client.cookies.delete("access_token")
    import asyncio
    await asyncio.sleep(1.1)
    response_login_email = await client.post(
        "/api/auth/login",
        data={"username": "admin@example.com", "password": "adminpassword"}
    )
    assert response_login_email.status_code == status.HTTP_200_OK
    login_email_data = response_login_email.json()
    assert login_email_data["username"] == "admin"
    assert login_email_data["role"] == "ROLE_ADMIN"
    email_token = response_login_email.cookies["access_token"]

    # 6. Access /me with cookie should succeed
    # Set the cookie explicitly for the next request using the email login token
    client.cookies.set("access_token", email_token)
    response_me = await client.get("/api/auth/me")
    assert response_me.status_code == status.HTTP_200_OK
    me_data = response_me.json()
    assert me_data["username"] == "admin"
    assert me_data["role"] == "ROLE_ADMIN"
    token = email_token

    # 7. Logout should delete cookie and revoke session in DB
    response_logout = await client.post("/api/auth/logout")
    assert response_logout.status_code == status.HTTP_200_OK
    
    # The client might still have cookie in its state, clear it manually
    client.cookies.delete("access_token")

    # 8. Accessing /me after logout/revocation should fail even if we try to reuse the old cookie
    client.cookies.set("access_token", token)
    response_me_revoked = await client.get("/api/auth/me")
    assert response_me_revoked.status_code == status.HTTP_401_UNAUTHORIZED
    assert "revoked" in response_me_revoked.json()["detail"]
