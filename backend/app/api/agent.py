import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.config import settings
from app.services.agent_coordinator import agent_coordinator

router = APIRouter(prefix="/agent", tags=["agent"])

@router.websocket("/ws")
async def agent_websocket_endpoint(websocket: WebSocket):
    # Accept the initial WebSocket connection
    await websocket.accept()
    
    try:
        # Wait for registration handshake
        registration_text = await websocket.receive_text()
        try:
            reg_data = json.loads(registration_text)
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid JSON payload")
            return
            
        if reg_data.get("type") != "register" or reg_data.get("token") != settings.AGENT_TOKEN:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token")
            return
            
        # Register the agent in coordinator
        await agent_coordinator.register(websocket)
        
        # Listen for messages from local agent
        while True:
            msg_text = await websocket.receive_text()
            await agent_coordinator.process_agent_message(msg_text)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[Agent Router Error]: {str(e)}")
    finally:
        # If this websocket is currently the registered agent, disconnect it
        if agent_coordinator.ws == websocket:
            agent_coordinator.disconnect()
