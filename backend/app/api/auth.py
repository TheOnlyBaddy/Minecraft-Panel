from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.api.deps import get_current_user, login_limiter
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepository
from app.core.security import create_access_token, get_password_hash, verify_password
from app.config import settings
from app.models.user import User
from app.services.audit_service import audit_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", dependencies=[Depends(login_limiter)])
async def login(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Authenticate credentials
    user = await AuthService.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    
    # Generate token
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.id, expires_delta=expires_delta)
    expires_at = datetime.utcnow() + expires_delta
    
    # Log session to database
    await AuthService.create_session(db, user.id, token, expires_at)
    
    # Audit log successful login
    await audit_service.log(
        db=db,
        user_id=user.id,
        action="LOGIN",
        target="auth",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={"username": user.username}
    )
    
    # Set secure HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=settings.is_remote_mode,  # Set to True in production/remote mode
        samesite="none" if settings.is_remote_mode else "lax"  # Allow cross-domain cookies in production
    )
    
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        # Mark token as revoked in database
        await AuthService.revoke_session(db, cookie_token)
        
    # Audit log logout event
    await audit_service.log(
        db=db,
        user_id=current_user.id,
        action="LOGOUT",
        target="auth",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={"username": current_user.username}
    )
        
    # Delete access_token cookie
    response.delete_cookie(key="access_token")
    return {"status": "success", "detail": "Logged out successfully"}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }

from pydantic import BaseModel, Field

class ChangePasswordPayload(BaseModel):
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

@router.put("/change-password")
async def change_password(
    payload: ChangePasswordPayload,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify current password is correct
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    if payload.new_password == payload.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password"
        )

    # Hash and save the new password
    current_user.password_hash = get_password_hash(payload.new_password)
    await db.commit()

    # Audit log the password change
    await audit_service.log(
        db=db,
        user_id=current_user.id,
        action="CHANGE_PASSWORD",
        target="auth",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={"username": current_user.username}
    )

    return {"status": "success", "detail": "Password changed successfully"}

@router.post("/seed")
async def seed_database(db: AsyncSession = Depends(get_db)):
    # Check if database is already seeded
    result = await db.execute(select(User))
    first_user = result.scalars().first()
    if first_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database has already been seeded with a user"
        )
    
    # Create default admin user
    admin_password = "adminpassword"
    admin_hash = get_password_hash(admin_password)
    admin_user = await UserRepository.create(
        db,
        username="admin",
        email="admin@example.com",
        password_hash=admin_hash,
        role="ROLE_ADMIN"
    )
    
    return {
        "status": "success",
        "detail": "Created default profiles",
        "accounts": [
            {"username": "admin", "password": admin_password, "role": admin_user.role}
        ]
    }
