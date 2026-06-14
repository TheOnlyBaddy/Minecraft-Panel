import json
import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.audit_service import audit_service

@pytest.mark.asyncio
async def test_audit_service_log(db: AsyncSession):
    # Setup test user
    user = User(username="testuser", email="testuser@example.com", password_hash="hash", role="ROLE_ADMIN")
    db.add(user)
    await db.commit()

    # Log action using service
    log_entry = await audit_service.log(
        db=db,
        user_id=user.id,
        action="TEST_ACTION",
        target="test_target",
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0",
        details={"foo": "bar"}
    )

    assert log_entry.id is not None
    assert log_entry.action == "TEST_ACTION"
    assert log_entry.target == "test_target"
    assert log_entry.ip_address == "127.0.0.1"
    assert log_entry.user_agent == "Mozilla/5.0"
    assert json.loads(log_entry.details_json) == {"foo": "bar"}

    # Retrieve from DB and assert
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_entry.id))
    db_entry = result.scalars().first()
    assert db_entry is not None
    assert db_entry.user_id == user.id

@pytest.mark.asyncio
async def test_audit_api_rbac_restrictions(client: AsyncClient, db: AsyncSession):
    # Seed database
    await client.post("/api/auth/seed")

    # Create a non-admin user manually
    from app.core.security import get_password_hash
    from app.repositories.user_repo import UserRepository
    user_hash = get_password_hash("userpassword")
    await UserRepository.create(
        db,
        username="test_user",
        email="test_user@example.com",
        password_hash=user_hash,
        role="ROLE_USER"
    )
    await db.commit()

    # Login non-admin
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "test_user", "password": "userpassword"}
    )
    assert login_resp.status_code == status.HTTP_200_OK
    user_token = login_resp.cookies["access_token"]

    # Attempt to read audit logs as non-admin (should fail with 403 Forbidden)
    client.cookies.set("access_token", user_token)
    get_resp = await client.get("/api/audit")
    assert get_resp.status_code == status.HTTP_403_FORBIDDEN

    # Login Admin
    await client.post("/api/auth/logout")
    client.cookies.delete("access_token")

    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert login_resp.status_code == status.HTTP_200_OK
    admin_token = login_resp.cookies["access_token"]

    # Read audit logs as Admin (should succeed with 200 OK)
    client.cookies.set("access_token", admin_token)
    get_resp = await client.get("/api/audit")
    assert get_resp.status_code == status.HTTP_200_OK
    assert "records" in get_resp.json()
    assert "total" in get_resp.json()

@pytest.mark.asyncio
async def test_audit_api_filters_and_pagination(client: AsyncClient, db: AsyncSession):
    # 1. Seed database & authenticate as Admin
    await client.post("/api/auth/seed")
    login_resp = await client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert login_resp.status_code == status.HTTP_200_OK
    admin_token = login_resp.cookies["access_token"]
    client.cookies.set("access_token", admin_token)

    # Setup mock audit logs in database
    # Get Admin and create a secondary test user
    res = await db.execute(select(User).where(User.username == "admin"))
    admin = res.scalars().first()
    
    from app.core.security import get_password_hash
    from app.repositories.user_repo import UserRepository
    user_hash = get_password_hash("otherpassword")
    other_user = await UserRepository.create(
        db,
        username="other_user",
        email="other_user@example.com",
        password_hash=user_hash,
        role="ROLE_ADMIN"
    )
    await db.commit()

    # Create logs directly in DB
    log1 = AuditLog(user_id=admin.id, action="LOGIN", target="auth", ip_address="127.0.0.1", user_agent="Chrome", details_json='{"username": "admin"}')
    log2 = AuditLog(user_id=other_user.id, action="LOGIN", target="auth", ip_address="192.168.1.5", user_agent="Firefox", details_json='{"username": "other_user"}')
    log3 = AuditLog(user_id=admin.id, action="UPDATE_CONFIG", target="server.properties", ip_address="127.0.0.1", user_agent="Chrome", details_json='{"max-players": 100}')
    log4 = AuditLog(user_id=admin.id, action="SERVER_LIFECYCLE", target="server", ip_address="127.0.0.1", user_agent="Chrome", details_json='{"action": "restart"}')
    log5 = AuditLog(user_id=admin.id, action="CREATE_BACKUP", target="backup", ip_address="127.0.0.1", user_agent="Chrome", details_json='{"filename": "backup1.zip"}')
    
    db.add_all([log1, log2, log3, log4, log5])
    await db.commit()

    # 3. Test Action Filter
    resp = await client.get("/api/audit?action=LOGIN")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["total"] >= 2
    assert all(r["action"] == "LOGIN" for r in data["records"])

    # 4. Test Username Filter
    resp = await client.get("/api/audit?username=other_user")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["total"] == 1
    assert data["records"][0]["username"] == "other_user"

    # 5. Test Search Filter (Target matches)
    resp = await client.get("/api/audit?search=properties")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["total"] == 1
    assert data["records"][0]["target"] == "server.properties"

    # Search Filter (Details matches)
    resp = await client.get("/api/audit?search=backup1")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["total"] == 1
    assert "backup1.zip" in data["records"][0]["details"]

    # 6. Test Pagination
    # Fetch page=1, limit=2
    resp = await client.get("/api/audit?limit=2&page=1")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert len(data["records"]) == 2
    assert data["total"] >= 5 # 5 mock entries + login audit trails

    # Fetch page=2, limit=2
    resp_page2 = await client.get("/api/audit?limit=2&page=2")
    assert resp_page2.status_code == status.HTTP_200_OK
    data_page2 = resp_page2.json()
    assert len(data_page2["records"]) == 2
    # Ensure no overlap of records
    ids_page1 = [r["id"] for r in data["records"]]
    ids_page2 = [r["id"] for r in data_page2["records"]]
    assert not set(ids_page1).intersection(set(ids_page2))
