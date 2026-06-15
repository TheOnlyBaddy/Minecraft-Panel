import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient
from app.main import app as fastapi_app
from app.db.session import get_db
from app.models.base import Base
import app.models
from app.config import settings

# Disable remote agent mode for tests
settings.AGENT_TOKEN = ""

# Mock shutil.which to prevent host playit.exe detection during testing
import shutil
shutil.which = lambda *args, **kwargs: None

# Memory-backed SQLite engine for isolated test environments
DATABASE_URL_TEST = "sqlite+aiosqlite:///./test.db"

engine_test = create_async_engine(
    DATABASE_URL_TEST,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = async_sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_db():
    print("\n--- SQLALCHEMY REGISTERED TABLES:", list(Base.metadata.tables.keys()), "---\n")
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine_test.dispose()
    import os
    for filename in ["test.db", "test.db-wal", "test.db-shm"]:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass

@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
        # Clear database records after each test run
        await session.rollback()

@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    async with engine_test.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Dependency override to use the testing session
    async def override_get_db():
        try:
            yield db
        finally:
            await db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        yield ac
        
    fastapi_app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def reset_process_manager():
    from app.services.process_manager import process_manager
    process_manager.status = "STOPPED"
    process_manager.process = None
    process_manager.log_buffer = []
    process_manager.active_players_set = set()
    yield
    process_manager.status = "STOPPED"
    process_manager.process = None
    process_manager.log_buffer = []
    process_manager.active_players_set = set()

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from app.api.deps import login_limiter
    login_limiter.history.clear()
    yield
    login_limiter.history.clear()
