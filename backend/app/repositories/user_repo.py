from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.db.mongodb import mongodb_manager

def map_mongo_user(doc: dict | None) -> User | None:
    if not doc:
        return None
    user = User(
        id=doc["id"],
        username=doc["username"],
        email=doc["email"],
        password_hash=doc["password_hash"],
        role=doc["role"]
    )
    if "created_at" in doc:
        user.created_at = doc["created_at"]
    if "updated_at" in doc:
        user.updated_at = doc["updated_at"]
    return user

class UserRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        if mongodb_manager.is_active:
            doc = await mongodb_manager.get_user_by_id(user_id)
            return map_mongo_user(doc)
            
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> User | None:
        if mongodb_manager.is_active:
            doc = await mongodb_manager.get_user_by_username(username)
            return map_mongo_user(doc)

        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        if mongodb_manager.is_active:
            doc = await mongodb_manager.get_user_by_email(email)
            return map_mongo_user(doc)

        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def get_by_username_or_email(db: AsyncSession, login_id: str) -> User | None:
        if mongodb_manager.is_active:
            doc = await mongodb_manager.get_user_by_username_or_email(login_id)
            return map_mongo_user(doc)

        result = await db.execute(
            select(User).where((User.username == login_id) | (User.email == login_id))
        )
        return result.scalars().first()

    @staticmethod
    async def create(db: AsyncSession, username: str, email: str, password_hash: str, role: str) -> User:
        if mongodb_manager.is_active:
            doc = await mongodb_manager.create_user(username, email, password_hash, role)
            return map_mongo_user(doc)

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
        if mongodb_manager.is_active:
            docs = await mongodb_manager.get_all_users()
            return [map_mongo_user(d) for d in docs if d]

        result = await db.execute(select(User).order_by(User.id))
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> None:
        if mongodb_manager.is_active:
            await mongodb_manager.delete_user(user.id)
            return

        await db.delete(user)
        await db.commit()
