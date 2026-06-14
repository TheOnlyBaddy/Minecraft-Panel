from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.backup import Backup

class BackupRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        filename: str,
        filepath: str,
        file_size: int,
        checksum: str,
        status: str = "PENDING",
        created_by: int | None = None
    ) -> Backup:
        backup = Backup(
            filename=filename,
            filepath=filepath,
            file_size=file_size,
            checksum=checksum,
            status=status,
            created_by=created_by
        )
        db.add(backup)
        await db.commit()
        await db.refresh(backup)
        return backup

    @staticmethod
    async def get_by_id(db: AsyncSession, backup_id: int) -> Backup | None:
        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        return result.scalars().first()

    @staticmethod
    async def list_all(db: AsyncSession) -> list[Backup]:
        result = await db.execute(select(Backup).order_by(Backup.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, backup: Backup) -> None:
        await db.delete(backup)
        await db.commit()

    @staticmethod
    async def update_status(db: AsyncSession, backup: Backup, status: str) -> Backup:
        backup.status = status
        await db.commit()
        await db.refresh(backup)
        return backup
