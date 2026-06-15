import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.db.mongodb import mongodb_manager

def map_mongo_audit(doc: dict | None) -> AuditLog | None:
    if not doc:
        return None
    audit = AuditLog(
        id=doc["id"],
        user_id=doc["user_id"],
        action=doc["action"],
        target=doc["target"],
        ip_address=doc["ip_address"],
        user_agent=doc["user_agent"],
        details_json=json.dumps(doc["details"]) if doc.get("details") else None
    )
    if "timestamp" in doc:
        audit.timestamp = doc["timestamp"]
    return audit

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
        if mongodb_manager.is_active:
            doc = await mongodb_manager.create_audit_log(
                user_id=user_id,
                action=action,
                target=target,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details
            )
            return map_mongo_audit(doc)

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
