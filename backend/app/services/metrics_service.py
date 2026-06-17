import os
import psutil
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import WebSocket
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.config import settings
from app.models.metric import Metric

class MetricsService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MetricsService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.active_connections: list[WebSocket] = []
            self.is_running = False
            self.session_factory = None
            self._loop_task = None
            self.latest_agent_metrics = None
            self._initialized = True

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        # Create a copy of connections list to avoid modifying during iteration
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception:
                # Remove stale or dead connections
                self.disconnect(connection)

    async def start(self, session_factory: async_sessionmaker[AsyncSession]):
        if self.is_running:
            return
        
        self.is_running = True
        self.session_factory = session_factory
        self._loop_task = asyncio.create_task(self._metrics_loop())

    async def stop(self):
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            self._loop_task = None

    def get_current_metrics(self) -> dict:
        # Fetch CPU and RAM using psutil
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        
        # Disk usage of the Minecraft folder
        server_dir = os.path.abspath(settings.MINECRAFT_SERVER_DIR)
        os.makedirs(server_dir, exist_ok=True)
        disk = psutil.disk_usage(server_dir)
        
        # Import process_manager dynamically to get player counts and status
        from app.services.process_manager import process_manager
        
        # Calculate active players from set size
        active_players_set = getattr(process_manager, "active_players_set", set())
        active_players = len(active_players_set)
        active_players_list = sorted(list(active_players_set))
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_percent": cpu,
            "memory_used": mem.used,
            "memory_total": mem.total,
            "disk_used": disk.used,
            "disk_total": disk.total,
            "active_players": active_players,
            "active_players_list": active_players_list,
            "server_status": process_manager.status,
            "server_address": settings.MINECRAFT_SERVER_ADDR,
            "minecraft_version": settings.MINECRAFT_VERSION,
            "agent_connected": True
        }

    def feed_agent_metrics(self, data: dict):
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu_percent": data.get("cpu_percent", 0.0),
            "memory_used": data.get("memory_used", 0),
            "memory_total": data.get("memory_total", 0),
            "disk_used": data.get("disk_used", 0),
            "disk_total": data.get("disk_total", 0),
            "active_players": data.get("active_players", 0),
            "active_players_list": data.get("active_players_list", []),
            "server_status": data.get("server_status", "STOPPED"),
            "server_address": settings.MINECRAFT_SERVER_ADDR,
            "minecraft_version": settings.MINECRAFT_VERSION,
            "agent_connected": True
        }
        self.latest_agent_metrics = metrics
        
        # Broadcast to UI clients immediately
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.broadcast(metrics))
        except Exception:
            pass

    async def _metrics_loop(self):
        counter = 0
        from app.db.session import SessionLocal
        
        while self.is_running:
            try:
                if settings.is_remote_mode:
                    from app.services.agent_coordinator import agent_coordinator
                    if not agent_coordinator.is_connected:
                        self.latest_agent_metrics = None
                        # Broadcast offline state
                        metrics = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "cpu_percent": 0.0,
                            "memory_used": 0,
                            "memory_total": 0,
                            "disk_used": 0,
                            "disk_total": 0,
                            "active_players": 0,
                            "active_players_list": [],
                            "server_status": "OFFLINE",
                            "server_address": settings.MINECRAFT_SERVER_ADDR,
                            "minecraft_version": settings.MINECRAFT_VERSION,
                            "agent_connected": False
                        }
                        if self.active_connections:
                            await self.broadcast(metrics)
                        await asyncio.sleep(2)
                        continue
                        
                    metrics = self.latest_agent_metrics
                    if metrics is None:
                        await asyncio.sleep(2)
                        continue
                else:
                    metrics = self.get_current_metrics()
                    # 1. Broadcast to all active WebSocket connections
                    if self.active_connections:
                        await self.broadcast(metrics)
                
                # 2. Write to SQLite once every 60 seconds (30 iterations of 2 seconds)
                counter += 1
                if counter >= 30:
                    counter = 0
                    session_factory = self.session_factory or SessionLocal
                    async with session_factory() as db:
                        metric_db = Metric(
                            cpu_percent=metrics["cpu_percent"],
                            memory_used=metrics["memory_used"],
                            memory_total=metrics["memory_total"],
                            disk_used=metrics["disk_used"],
                            active_players=metrics["active_players"]
                        )
                        db.add(metric_db)
                        
                        # 3. Hourly database cleanup (prune metrics older than 30 days)
                        # Clean once per hour (approx 1800 iterations at 2-sec intervals)
                        # Let's run it here during DB write to make it simple
                        if datetime.now().minute == 0:
                            cutoff = datetime.utcnow() - timedelta(days=30)
                            await db.execute(delete(Metric).where(Metric.timestamp < cutoff))
                            
                        await db.commit()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error or suppress during loop
                print(f"[Metrics Loop Error]: {str(e)}")
            
            # Gather metrics every 2 seconds
            await asyncio.sleep(2)

# Instantiate singleton metrics service
metrics_service = MetricsService()
