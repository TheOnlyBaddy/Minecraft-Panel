import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import engine, SessionLocal
from app.models.base import Base
from app.api import auth, server, telemetry, console, backup, config, audit, players, files, worlds, users, plugins
from app.services.metrics_service import metrics_service

app = FastAPI(
    title="Antigravity Panel API",
    description="Backend service for Minecraft Server Management Panel",
    version="0.1.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:;"
    )
    return response

# Startup DB tables creator
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # Create all tables defined in models on startup if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    # Start metrics gathering loop
    await metrics_service.start(SessionLocal)

@app.on_event("shutdown")
async def on_shutdown():
    # Stop metrics loop
    await metrics_service.stop()

# Mount Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(server.router, prefix=settings.API_V1_STR)
app.include_router(telemetry.router, prefix=settings.API_V1_STR)
app.include_router(console.router, prefix=settings.API_V1_STR)
app.include_router(backup.router, prefix=settings.API_V1_STR)
app.include_router(config.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(players.router, prefix=settings.API_V1_STR)
app.include_router(files.router, prefix=settings.API_V1_STR)
app.include_router(worlds.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(plugins.router, prefix=settings.API_V1_STR)

@app.get("/api/info")
async def get_panel_info():
    return {
        "panel_name": settings.PANEL_NAME,
        "minecraft_version": settings.MINECRAFT_VERSION
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Antigravity Panel"}
