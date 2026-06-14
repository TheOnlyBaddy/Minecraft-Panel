from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.api.deps import require_admin
from app.repositories.user_repo import UserRepository
from app.core.security import get_password_hash
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

class UserCreatePayload(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=6, description="Password")

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    
    class Config:
        from_attributes = True

@router.get("", response_model=list[UserResponse])
async def list_panel_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    users = await UserRepository.get_all(db)
    return users

@router.post("", response_model=UserResponse)
async def create_panel_user(
    payload: UserCreatePayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the primary 'admin' account is authorized to manage users."
        )

    username = payload.username.strip()
    email = payload.email.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if not email:
        raise HTTPException(status_code=400, detail="Email cannot be empty")
        
    existing_user = await UserRepository.get_by_username(db, username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    existing_email = await UserRepository.get_by_email(db, email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    hashed_password = get_password_hash(payload.password)
    new_user = await UserRepository.create(
        db=db,
        username=username,
        email=email,
        password_hash=hashed_password,
        role="ROLE_ADMIN"
    )
    return new_user

@router.delete("/{user_id}")
async def delete_panel_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the primary 'admin' account is authorized to manage users."
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own active administrator account."
        )
        
    user = await UserRepository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    await UserRepository.delete(db, user)
    return {"status": "success", "detail": f"User '{user.username}' successfully deleted."}
