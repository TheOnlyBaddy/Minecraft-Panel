import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import require_admin, require_moderator
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.config_service import config_service

router = APIRouter(prefix="/server/config", tags=["config"])

@router.get("")
async def get_server_configuration(
    current_user: User = Depends(require_moderator)
):
    try:
        config = await config_service.get_config()
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read configuration: {str(e)}"
        )

@router.post("")
async def update_server_configuration(
    payload: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must be a JSON object of configuration key-value properties."
        )

    try:
        updated_config = await config_service.save_config(db, payload, current_user.id)
        
        # Commit write action to audit logs
        audit = AuditLog(
            user_id=current_user.id,
            action="UPDATE_CONFIG",
            target="server.properties",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details_json=json.dumps(payload)
        )
        db.add(audit)
        await db.commit()

        # Trigger auto-restart if server is active (STARTING or RUNNING)
        from app.services.process_manager import process_manager
        import asyncio
        if process_manager.status in ("STARTING", "RUNNING"):
            async def auto_restart():
                process_manager._append_log("[Panel]: Server configuration updated. Triggering auto-restart...")
                try:
                    await process_manager.stop()
                    await asyncio.sleep(2)
                    await process_manager.start()
                except Exception as e:
                    process_manager._append_log(f"[Panel Error]: Auto-restart failed: {str(e)}")
            
            asyncio.create_task(auto_restart())

        return {"status": "success", "detail": "Configuration updated successfully", "config": updated_config}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save configuration: {str(e)}"
        )
