from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.repositories.user_repo import UserRepository
from app.core.security import verify_password
from app.models.user import User
from app.models.session import Session
from app.db.mongodb import mongodb_manager

def map_mongo_session(doc: dict | None) -> Session | None:
    if not doc:
        return None
    session = Session(
        user_id=doc["user_id"],
        session_token=doc["session_token"],
        expires_at=doc["expires_at"],
        is_revoked=doc["is_revoked"]
    )
    return session

class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, username_or_email: str, password: str) -> User | None:
        user = await UserRepository.get_by_username_or_email(db, username_or_email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    async def create_session(db: AsyncSession, user_id: int, token: str, expires_at: datetime) -> Session:
        if mongodb_manager.is_active:
            doc = await mongodb_manager.create_session(user_id, token, expires_at)
            return map_mongo_session(doc)

        session = Session(
            user_id=user_id,
            session_token=token,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def revoke_session(db: AsyncSession, token: str) -> bool:
        if mongodb_manager.is_active:
            return await mongodb_manager.revoke_session(token)

        result = await db.execute(select(Session).where(Session.session_token == token))
        session = result.scalars().first()
        if session:
            session.is_revoked = True
            await db.commit()
            return True
        return False

    @staticmethod
    async def is_session_revoked(db: AsyncSession, token: str) -> bool:
        if mongodb_manager.is_active:
            return await mongodb_manager.is_session_revoked(token)

        result = await db.execute(select(Session).where(Session.session_token == token))
        session = result.scalars().first()
        if session:
            return session.is_revoked
        return True
