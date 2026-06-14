import json
import re
from fastapi import APIRouter, WebSocket, status, Depends, Request, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import decode_access_token
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.services.console_service import console_service
from app.services.process_manager import process_manager
from app.models.audit_log import AuditLog
from app.api.deps import require_moderator
from app.models.user import User

router = APIRouter(prefix="/server", tags=["server"])

class CommandPayload(BaseModel):
    command: str = Field(..., min_length=1, max_length=1000, description="Console command to execute")

@router.post("/console/command")
async def execute_console_command(
    payload: CommandPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_moderator)
):
    command = payload.command.strip()[:256].strip()
    if not command:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Command cannot be empty"
        )
    
    # Reject newlines or carriage returns to prevent command pipeline chaining/injection in stdin
    if "\n" in command or "\r" in command:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Newline or carriage return characters are not permitted."
        )

    # Enforce character whitelist pattern
    if not re.match(r"^[a-zA-Z0-9\s_\-\/\?\!\:]+$", command):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Command contains forbidden characters."
        )

    # Write command to subprocess stdin
    await process_manager.write_stdin(command)

    # Commit execution action to audit logs
    audit = AuditLog(
        user_id=current_user.id,
        action="EXECUTE_COMMAND",
        target="server",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details_json=json.dumps({"command": command})
    )
    db.add(audit)
    await db.commit()

    return {"status": "success", "detail": "Command submitted successfully"}

@router.websocket("/console")
async def stream_console(
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
        
    # Register connection to console service broadcast pool
    await console_service.connect(websocket)

    # Push the current log buffer history
    try:
        await websocket.send_json({
            "type": "history",
            "lines": list(process_manager.log_buffer)
        })
    except Exception:
        console_service.disconnect(websocket)
        return
    
    try:
        # Keep WebSocket connection alive and listen for client disconnects
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        console_service.disconnect(websocket)
