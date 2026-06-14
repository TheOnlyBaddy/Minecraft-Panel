from fastapi import APIRouter, WebSocket, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import decode_access_token
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.services.metrics_service import metrics_service

router = APIRouter(prefix="/server", tags=["server"])

@router.websocket("/telemetry")
async def stream_telemetry(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    # Retrieve JWT from session cookies
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session cookie missing")
        return
        
    # Verify session is valid and not revoked
    is_revoked = await AuthService.is_session_revoked(db, token)
    if is_revoked:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Session revoked")
        return
        
    # Extract user payload details
    user_id_str = decode_access_token(token)
    if not user_id_str:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
        
    try:
        user_id = int(user_id_str)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Malformed token ID")
        return
        
    user = await UserRepository.get_by_id(db, user_id)
    if not user or user.role != "ROLE_ADMIN":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return
        
    # Register connection to metrics service broadcast pool
    await metrics_service.connect(websocket)
    
    try:
        # Keep WebSocket connection alive and listen for client disconnects
        while True:
            # We discard any incoming client frames as this is a push-only statistics channel
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        metrics_service.disconnect(websocket)
