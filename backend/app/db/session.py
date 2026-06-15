from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

# Create async engine with pool settings
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # Disable prepared statement cache for PostgreSQL to support PgBouncer/Supabase transaction pooler
    connect_args["prepared_statement_cache_size"] = 0
    connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

# SQLite optimization event listener
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if db_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.close()

# Async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Dependency to get db session
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
