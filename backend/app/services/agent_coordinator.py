import uuid
import json
import asyncio
from fastapi import WebSocket
from app.config import settings

class AgentCoordinator:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AgentCoordinator, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.ws: WebSocket = None
            self.pending_requests: dict[str, asyncio.Future] = {}
            self._initialized = True

    @property
    def is_connected(self) -> bool:
        return self.ws is not None

    async def register(self, ws: WebSocket):
        # Disconnect any existing agent first
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
        self.ws = ws
        print("[Agent Coordinator]: Local agent connected and registered.")

    def disconnect(self):
        self.ws = None
        print("[Agent Coordinator]: Local agent disconnected.")
        # Cancel all pending requests
        for req_id, fut in list(self.pending_requests.items()):
            if not fut.done():
                fut.set_exception(RuntimeError("Agent disconnected before response was received."))
        self.pending_requests.clear()

    async def send_request(self, mtype: str, payload: dict = None) -> dict:
        if not self.is_connected:
            raise RuntimeError("Minecraft Local Agent is offline. Please make sure the agent is running on your local PC.")

        req_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self.pending_requests[req_id] = fut

        msg = {
            "type": mtype,
            "request_id": req_id
        }
        if payload:
            msg.update(payload)

        try:
            await self.ws.send_json(msg)
            # 20 seconds timeout for agent file operations/backups
            response = await asyncio.wait_for(fut, timeout=25.0)
            return response
        except asyncio.TimeoutError:
            raise RuntimeError(f"Request '{mtype}' timed out waiting for local agent response.")
        finally:
            self.pending_requests.pop(req_id, None)

    async def process_agent_message(self, message_str: str):
        try:
            msg = json.loads(message_str)
        except Exception as e:
            print(f"[Agent Coordinator Error]: Malformed agent payload: {e}")
            return

        mtype = msg.get("type", "")
        
        # 1. Check for request-response completion
        if mtype.endswith("_response"):
            req_id = msg.get("request_id")
            if req_id and req_id in self.pending_requests:
                fut = self.pending_requests[req_id]
                if not fut.done():
                    fut.set_result(msg)
            return

        # 2. Status update
        if mtype == "status_update":
            from app.services.process_manager import process_manager
            process_manager.status = msg.get("status", "STOPPED")
            return

        # 3. Stream log output
        if mtype == "log":
            from app.services.process_manager import process_manager
            # Forward log output to backend's ProcessManager to buffer and broadcast
            process_manager._append_log_direct(msg.get("line", ""))
            return

        # 4. Metrics packet feed
        if mtype == "metrics":
            from app.services.metrics_service import metrics_service
            metrics_service.feed_agent_metrics(msg.get("data", {}))
            return

# Instantiate singleton agent coordinator
agent_coordinator = AgentCoordinator()
