import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-panel-key-change-in-production-123456")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # SQLite Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    
    # Minecraft Configuration
    MINECRAFT_SERVER_DIR: str = os.getenv(
        "MINECRAFT_SERVER_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Minecraft Server"))
    )
    MINECRAFT_JAR_NAME: str = "paper.jar"
    MINECRAFT_MIN_RAM: str = "6G"
    MINECRAFT_MAX_RAM: str = "6G"
    MINECRAFT_SERVER_ADDR: str = os.getenv("MINECRAFT_SERVER_ADDR", "192.168.1.13:25565")
    MINECRAFT_VERSION: str = os.getenv("MINECRAFT_VERSION", "26.1.2")
    # Panel Branding Name
    PANEL_NAME: str = os.getenv("PANEL_NAME", "DEEP SURVIVAL")

    class Config:
        case_sensitive = True

settings = Settings()
