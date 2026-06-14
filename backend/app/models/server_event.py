from datetime import datetime
from sqlalchemy import String, DateTime, Integer, text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class ServerEvent(Base):
    __tablename__ = "server_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. 'START', 'STOP', 'CRASH', 'SIGKILL'
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"), index=True)
