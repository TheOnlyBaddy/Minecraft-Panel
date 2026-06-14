import time
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import decode_access_token
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.models.user import User

async def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing session cookie.",
        )
    return token

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session cookie missing",
        )
    
    # Check if session token has been revoked in database
    is_revoked = await AuthService.is_session_revoked(db, token)
    if is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked/logged out",
        )
    
    # Decode token payload
    user_id_str = decode_access_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed session identifier",
        )
        
    user = await UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user

class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires roles: {self.allowed_roles}. Current role: {current_user.role}",
            )
        return current_user

# Predefined role dependency overrides
require_admin = RoleChecker(["ROLE_ADMIN"])
require_moderator = RoleChecker(["ROLE_ADMIN"])

class RateLimitGuard:
    """In-memory rate limiting dependency mapped to client IP addresses."""
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.history = {}

    async def __call__(self, request: Request):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        if ip not in self.history:
            self.history[ip] = []
        self.history[ip] = [t for t in self.history[ip] if now - t < self.window]
        
        if len(self.history[ip]) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
        self.history[ip].append(now)

login_limiter = RateLimitGuard(limit=5, window=60)
