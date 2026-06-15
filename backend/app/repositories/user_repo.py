from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User

class UserRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_by_username_or_email(db: AsyncSession, login_id: str) -> User | None:
        result = await db.execute(
            select(User).where((User.username == login_id) | (User.email == login_id))
        )
        return result.scalars().first()

    @staticmethod
    async def create(db: AsyncSession, username: str, email: str, password_hash: str, role: str) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_all(db: AsyncSession) -> list[User]:
        result = await db.execute(select(User).order_by(User.id))
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.commit()

