import re
import time
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

class MongoDBManager:
    def __init__(self):
        self._client = None
        self._db = None

    @property
    def is_active(self) -> bool:
        return bool(settings.MONGO_URL)

    def get_db(self):
        if not self.is_active:
            return None
        if self._db is None:
            # Connect lazily so it doesn't run during non-Mongo local tests
            self._client = AsyncIOMotorClient(settings.MONGO_URL)
            # Parse DB name from URL if possible, otherwise default to "minecraft_panel"
            # e.g., mongodb+srv://.../dbname?options
            match = re.search(r"/([^/?]+)(?:\?|$)", settings.MONGO_URL)
            db_name = match.group(1) if match else "minecraft_panel"
            self._db = self._client[db_name]
        return self._db

    async def get_next_sequence_value(self, sequence_name: str) -> int:
        db = self.get_db()
        counter = await db.counters.find_one_and_update(
            {"_id": sequence_name},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        return counter["seq"]

    # --- User Operations ---
    async def get_user_by_id(self, user_id: int) -> dict | None:
        db = self.get_db()
        user = await db.users.find_one({"id": user_id})
        return user

    async def get_user_by_username(self, username: str) -> dict | None:
        db = self.get_db()
        user = await db.users.find_one({"username_lower": username.lower()})
        return user

    async def get_user_by_email(self, email: str) -> dict | None:
        db = self.get_db()
        user = await db.users.find_one({"email_lower": email.lower()})
        return user

    async def get_user_by_username_or_email(self, login_id: str) -> dict | None:
        db = self.get_db()
        login_lower = login_id.lower()
        user = await db.users.find_one({
            "$or": [
                {"username_lower": login_lower},
                {"email_lower": login_lower}
            ]
        })
        return user

    async def create_user(self, username: str, email: str, password_hash: str, role: str) -> dict:
        user_id = await self.get_next_sequence_value("user_id")
        user = {
            "id": user_id,
            "username": username,
            "username_lower": username.lower(),
            "email": email,
            "email_lower": email.lower(),
            "password_hash": password_hash,
            "role": role,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        await self.get_db().users.insert_one(user)
        return user

    async def get_all_users(self) -> list[dict]:
        db = self.get_db()
        cursor = db.users.find().sort("id", 1)
        users = []
        async for doc in cursor:
            users.append(doc)
        return users

    async def delete_user(self, user_id: int) -> bool:
        db = self.get_db()
        res = await db.users.delete_one({"id": user_id})
        # Clean up user's active sessions too
        await db.sessions.delete_many({"user_id": user_id})
        return res.deleted_count > 0

    # --- Session Operations ---
    async def create_session(self, user_id: int, token: str, expires_at: datetime) -> dict:
        session = {
            "user_id": user_id,
            "session_token": token,
            "expires_at": expires_at.replace(tzinfo=timezone.utc),
            "is_revoked": False,
            "created_at": datetime.now(timezone.utc)
        }
        await self.get_db().sessions.insert_one(session)
        return session

    async def revoke_session(self, token: str) -> bool:
        db = self.get_db()
        res = await db.sessions.update_one(
            {"session_token": token},
            {"$set": {"is_revoked": True}}
        )
        return res.modified_count > 0

    async def is_session_revoked(self, token: str) -> bool:
        db = self.get_db()
        session = await db.sessions.find_one({"session_token": token})
        if session:
            # Check revocation and expiry
            expires_at = session.get("expires_at")
            if expires_at:
                # Make naive datetime from mongo offset-aware to compare
                expires_utc = expires_at.replace(tzinfo=timezone.utc)
                if expires_utc < datetime.now(timezone.utc):
                    return True
            return session.get("is_revoked", False)
        return True

    # --- Audit Log Operations ---
    async def create_audit_log(
        self,
        user_id: int | None,
        action: str,
        target: str,
        ip_address: str,
        user_agent: str,
        details: dict | None = None
    ) -> dict:
        audit_id = await self.get_next_sequence_value("audit_id")
        audit = {
            "id": audit_id,
            "user_id": user_id,
            "action": action,
            "target": target,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details,
            "timestamp": datetime.now(timezone.utc)
        }
        await self.get_db().audit_logs.insert_one(audit)
        return audit

    async def get_audit_logs(
        self,
        page: int = 1,
        limit: int = 50,
        action: str | None = None,
        username: str | None = None,
        search: str | None = None
    ) -> tuple[list[dict], int]:
        db = self.get_db()
        
        # Build filter query
        query = {}
        if action:
            query["action"] = action
        
        if username:
            # Find the user first to get the user_id
            user = await self.get_user_by_username(username)
            if user:
                query["user_id"] = user["id"]
            else:
                # Username doesn't exist, return empty list
                return [], 0

        if search:
            # Search target field or details object
            search_regex = re.compile(search, re.IGNORECASE)
            query["$or"] = [
                {"target": search_regex},
                {"action": search_regex},
                {"ip_address": search_regex},
                # Search keys/values inside details dict
                {"details.username": search_regex},
                {"details.file": search_regex}
            ]

        # Get total matching count
        total_count = await db.audit_logs.count_documents(query)

        # Get paginated records sorted by timestamp descending
        offset = (page - 1) * limit
        cursor = db.audit_logs.find(query).sort("timestamp", -1).skip(offset).limit(limit)
        
        records = []
        async for doc in cursor:
            # Resolve username dynamically
            u_id = doc.get("user_id")
            doc_user = await self.get_user_by_id(u_id) if u_id is not None else None
            doc["username"] = doc_user["username"] if doc_user else "System"
            records.append(doc)

        return records, total_count

mongodb_manager = MongoDBManager()
