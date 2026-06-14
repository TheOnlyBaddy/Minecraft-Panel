import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

class AuditLogService:
    @staticmethod
    async def log(
        db: AsyncSession,
        user_id: int | None,
        action: str,
        target: str,
        ip_address: str,
        user_agent: str,
        details: dict | None = None
    ) -> AuditLog:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            target=target,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=json.dumps(details) if details else None
        )
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        return audit

audit_service = AuditLogService()
