from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.models.audit_log import AuditLog
from typing import Optional

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("")
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Records per page"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    username: Optional[str] = Query(None, description="Filter by username of actor"),
    search: Optional[str] = Query(None, description="Search term matching target or details"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # Base query for selecting records and joining with User to retrieve the username
    query = select(AuditLog).options(selectinload(AuditLog.user)).outerjoin(User).order_by(AuditLog.timestamp.desc())
    count_query = select(func.count()).select_from(AuditLog).outerjoin(User)

    # Apply filters if provided
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    
    if username:
        query = query.where(User.username == username)
        count_query = count_query.where(User.username == username)
        
    if search:
        search_filter = (AuditLog.target.ilike(f"%{search}%")) | (AuditLog.details_json.ilike(f"%{search}%"))
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Calculate total count of records matching filters
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0

    # Retrieve paginated records
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    records_result = await db.execute(query)
    records = records_result.scalars().all()

    # Format output records
    serialized = []
    for log in records:
        serialized.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": log.user.username if log.user else "System",
            "action": log.action,
            "target": log.target,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "details": log.details_json # keep raw JSON string or let frontend parse it
        })

    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "records": serialized
    }
