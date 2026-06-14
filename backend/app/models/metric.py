from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP"), index=True)
    cpu_percent: Mapped[float] = mapped_column(Float, nullable=False)
    memory_used: Mapped[int] = mapped_column(Integer, nullable=False) # bytes
    memory_total: Mapped[int] = mapped_column(Integer, nullable=False) # bytes
    disk_used: Mapped[int] = mapped_column(Integer, nullable=False) # bytes
    active_players: Mapped[int] = mapped_column(Integer, nullable=False)
