import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from fastapi import status
from app.services.metrics_service import metrics_service
from app.models.metric import Metric
from tests.conftest import TestingSessionLocal
from sqlalchemy.future import select

@pytest_asyncio.fixture(autouse=True)
async def configure_metrics_test():
    # Force metrics service to use test session factory
    metrics_service.session_factory = TestingSessionLocal
    yield
    # Cleanup task loops to avoid pending asyncio warnings
    await metrics_service.stop()
    metrics_service.session_factory = None

@pytest.mark.asyncio
async def test_get_current_metrics():
    metrics = metrics_service.get_current_metrics()
    assert "cpu_percent" in metrics
    assert "memory_used" in metrics
    assert "memory_total" in metrics
    assert "disk_used" in metrics
    assert "disk_total" in metrics
    assert "active_players" in metrics
    assert "server_status" in metrics
    
    assert isinstance(metrics["cpu_percent"], (int, float))
    assert isinstance(metrics["memory_used"], int)
    assert isinstance(metrics["memory_total"], int)
    assert isinstance(metrics["disk_used"], int)
    assert isinstance(metrics["disk_total"], int)
    assert isinstance(metrics["active_players"], int)
    assert metrics["server_status"] == "STOPPED"

@pytest.mark.asyncio
async def test_telemetry_websocket_auth(db):
    from fastapi.testclient import TestClient
    from app.main import app as fastapi_app
    from app.db.session import get_db

    async def override_get_db():
        try:
            yield db
        finally:
            await db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db

    def run_websocket_test():
        test_client = TestClient(fastapi_app)
        # 1. Attempt connection without token cookie should fail
        with pytest.raises(Exception):
            with test_client.websocket_connect("/api/server/telemetry"):
                pass

        # 2. Seed database & login as admin
        seed_res = test_client.post("/api/auth/seed")
        assert seed_res.status_code == 200
        
        login_res = test_client.post("/api/auth/login", data={"username": "admin", "password": "adminpassword"})
        assert login_res.status_code == 200
        token = login_res.cookies.get("access_token")
        assert token is not None

        # 3. Connect to WebSocket telemetry with valid cookie
        test_client.cookies.set("access_token", token)

        with test_client.websocket_connect("/api/server/telemetry") as websocket:
            # Wait to receive a streamed telemetry frame
            data = websocket.receive_json()
            assert "cpu_percent" in data
            assert "memory_used" in data
            assert "server_status" in data
            assert data["server_status"] == "STOPPED"

    try:
        # Start background metrics service explicitly to push metrics frames
        await metrics_service.start(TestingSessionLocal)
        
        # Run the synchronous TestClient code in a separate thread so it doesn't block the main event loop
        await asyncio.to_thread(run_websocket_test)
    finally:
        fastapi_app.dependency_overrides.clear()
        await metrics_service.stop()

@pytest.mark.asyncio
async def test_metrics_database_logging(db):
    # clean_database autouse fixture already ran, so metrics table starts empty.
    
    # Manually trigger a DB save sequence
    metrics = metrics_service.get_current_metrics()
    metric_record = Metric(
        cpu_percent=metrics["cpu_percent"],
        memory_used=metrics["memory_used"],
        memory_total=metrics["memory_total"],
        disk_used=metrics["disk_used"],
        active_players=metrics["active_players"]
    )
    db.add(metric_record)
    await db.commit()
    
    # Query database and verify fields
    result = await db.execute(select(Metric))
    saved_metric = result.scalars().first()
    assert saved_metric is not None
    assert saved_metric.cpu_percent == metrics["cpu_percent"]
    assert saved_metric.memory_used == metrics["memory_used"]
