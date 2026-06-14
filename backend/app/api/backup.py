from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.deps import require_admin, require_moderator
from app.models.user import User
from app.repositories.backup_repo import BackupRepository
from app.services.backup_service import backup_service
from app.services.audit_service import audit_service

router = APIRouter(prefix="/backups", tags=["backups"])

def serialize_backup(backup):
    return {
        "id": backup.id,
        "filename": backup.filename,
        "filepath": backup.filepath,
        "file_size": backup.file_size,
        "checksum": backup.checksum,
        "status": backup.status,
        "created_by": backup.created_by,
        "created_at": backup.created_at.isoformat() if backup.created_at else None
    }

@router.post("")
async def trigger_manual_backup(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    try:
        backup = await backup_service.create_backup(db, current_user.id)
        
        # Log to audit logs
        await audit_service.log(
            db=db,
            user_id=current_user.id,
            action="CREATE_BACKUP",
            target="backup",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details={"filename": backup.filename}
        )

        return {"status": "success", "detail": "Backup created successfully", "backup": serialize_backup(backup)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup creation failed: {str(e)}"
        )

@router.get("")
async def list_all_backups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_moderator)
):
    backups = await BackupRepository.list_all(db)
    return [serialize_backup(b) for b in backups]

@router.post("/{backup_id}/restore")
async def restore_server_backup(
    backup_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    backup = await BackupRepository.get_by_id(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup record with id {backup_id} not found."
        )
    
    if backup.status != "SUCCESSFUL":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot restore a backup that is in status: {backup.status}"
        )

    try:
        await backup_service.restore_backup(db, backup)
        
        # Log to audit logs
        await audit_service.log(
            db=db,
            user_id=current_user.id,
            action="RESTORE_BACKUP",
            target="backup",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details={"filename": backup.filename, "backup_id": backup.id}
        )

        return {"status": "success", "detail": "Backup restoration completed and server rebooted."}
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restoration failed: {str(e)}"
        )

@router.delete("/{backup_id}")
async def delete_server_backup(
    backup_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    backup = await BackupRepository.get_by_id(db, backup_id)
    if not backup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup record with id {backup_id} not found."
        )

    try:
        await backup_service.delete_backup(db, backup)
        
        # Log to audit logs
        await audit_service.log(
            db=db,
            user_id=current_user.id,
            action="DELETE_BACKUP",
            target="backup",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details={"filename": backup.filename, "backup_id": backup.id}
        )

        return {"status": "success", "detail": "Backup file and database record deleted successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )
