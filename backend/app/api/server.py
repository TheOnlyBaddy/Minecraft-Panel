from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import require_moderator
from app.services.process_manager import process_manager, HTTPException as PMException
from app.services.audit_service import audit_service
from app.models.user import User

router = APIRouter(prefix="/server", tags=["server"])

class LifecycleAction(BaseModel):
    action: Literal["start", "stop", "restart", "kill"] = Field(..., description="Action to perform on server process")

@router.post("/lifecycle")
async def control_server_lifecycle(
    payload: LifecycleAction,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_moderator)
):
    action = payload.action
    
    try:
        # Commit action to audit logs before running
        await audit_service.log(
            db=db,
            user_id=current_user.id,
            action="SERVER_LIFECYCLE",
            target="server",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details={"action": action}
        )

        if action == "start":
            await process_manager.start()
            return {"status": "success", "detail": "Server start initiated", "state": process_manager.status}
        
        elif action == "stop":
            # Start stop task asynchronously to avoid blocking the API request thread during wait periods
            import asyncio
            asyncio.create_task(process_manager.stop())
            return {"status": "success", "detail": "Server stop initiated", "state": process_manager.status}
            
        elif action == "kill":
            await process_manager.kill()
            return {"status": "success", "detail": "Server force-killed", "state": process_manager.status}
            
        elif action == "restart":
            # Restart runs stop, then wait-start
            async def run_restart():
                await process_manager.stop()
                # Wait briefly for ports to flush
                await asyncio.sleep(2)
                await process_manager.start()
            
            import asyncio
            asyncio.create_task(run_restart())
            return {"status": "success", "detail": "Server restart initiated", "state": process_manager.status}
            
    except PMException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lifecycle action failed: {str(e)}"
        )

@router.get("/status")
async def get_server_status(current_user: User = Depends(require_moderator)):
    from app.config import settings
    return {
        "status": process_manager.status,
        "is_running": process_manager.status in ("STARTING", "RUNNING"),
        "server_address": settings.MINECRAFT_SERVER_ADDR
    }

@router.get("/logs")
async def get_console_logs(current_user: User = Depends(require_moderator)):
    return {
        "logs": process_manager.log_buffer
    }

@router.get("/logs/latest")
async def get_latest_log_file(current_user: User = Depends(require_moderator)):
    import os
    from app.config import settings
    log_path = os.path.abspath(os.path.join(settings.MINECRAFT_SERVER_DIR, "logs", "latest.log"))
    if not os.path.exists(log_path):
        return {"content": "Log file not found."}
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read latest log: {str(e)}"
        )

@router.post("/logs/clear")
async def clear_latest_log_file(current_user: User = Depends(require_moderator)):
    import os
    from app.config import settings
    log_path = os.path.abspath(os.path.join(settings.MINECRAFT_SERVER_DIR, "logs", "latest.log"))
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("")
        return {"status": "success", "detail": "Log file cleared successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear log: {str(e)}"
        )

