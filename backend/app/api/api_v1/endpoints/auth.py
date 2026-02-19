from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.core.email import send_password_reset_email
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    Token,
)
from app.schemas.user import UserCreate, UserResponse, PasswordChange
from app.services.password_reset import (
    create_reset_token,
    mark_token_used,
    validate_reset_token,
)
from app.api.deps import get_current_active_user
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()
settings = get_settings()

# Rate limiter instance (configured in main.py)
limiter = Limiter(key_func=get_remote_address)


def conditional_rate_limit(limit_string: str):
    """Apply rate limiting only if enabled in settings."""
    def decorator(func):
        if settings.RATE_LIMIT_ENABLED:
            return limiter.limit(limit_string)(func)
        return func
    return decorator


@router.post("/login", response_model=Token)
@conditional_rate_limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
@conditional_rate_limit("10/minute")
async def refresh_token(
    request: Request,
    refresh_data: RefreshRequest,
) -> Any:
    payload = decode_token(refresh_data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@conditional_rate_limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"User registered: {user.email}", extra={"user_id": user.id})
    return user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()

    logger.info(f"Password changed for user: {user.email}", extra={"user_id": user.id})


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
@conditional_rate_limit("3/hour")
async def forgot_password(
    request: Request,
    request_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Request password reset email.
    
    Always returns 204 to prevent email enumeration attacks.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == request_data.email))
    user = result.scalar_one_or_none()
    
    # Always return 204 to prevent email enumeration
    if not user:
        return
    
    # Create reset token
    token = await create_reset_token(user.id, db)
    
    # Generate reset URL
    frontend_url = settings.FRONTEND_URL or "http://localhost:5173"
    reset_url = f"{frontend_url}/reset-password?token={token}"
    
    # Send email
    await send_password_reset_email(user.email, user.first_name, reset_url)
    
    logger.info(f"Password reset requested for: {user.email}")


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Reset password with token."""
    # Validate token
    user = await validate_reset_token(reset_data.token, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    
    # Mark token as used
    await mark_token_used(reset_data.token, db)
    
    await db.commit()
    
    logger.info(f"Password reset completed for: {user.email}")
