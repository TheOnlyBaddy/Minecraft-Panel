import asyncio
from fastapi import WebSocket

class ConsoleService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConsoleService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.active_connections: list[WebSocket] = []
            self._initialized = True

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, log_line: str):
        # We broadcast the log line to all active connections
        for connection in list(self.active_connections):
            try:
                # We send the log line as a text frame
                await connection.send_json({"type": "log", "line": log_line})
            except Exception:
                # Remove dead/broken connections
                self.disconnect(connection)

console_service = ConsoleService()
