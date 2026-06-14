import asyncio
from app.db.session import SessionLocal
from app.models.server_event import ServerEvent
from app.models.audit_log import AuditLog
from sqlalchemy.future import select

async def main():
    async with SessionLocal() as db:
        # Get server events
        res = await db.execute(select(ServerEvent).order_by(ServerEvent.timestamp.desc()).limit(10))
        events = res.scalars().all()
        print("--- Server Events ---")
        for e in events:
            print(f"[{e.timestamp}] {e.event_type}: {e.description} (Exit Code: {e.exit_code})")
            
        # Get latest audit logs
        res2 = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10))
        audits = res2.scalars().all()
        print("\n--- Latest Audit Logs ---")
        for a in audits:
            print(f"[{a.timestamp}] User {a.user_id} - Action {a.action} on {a.target}: {a.details_json}")

if __name__ == "__main__":
    asyncio.run(main())
