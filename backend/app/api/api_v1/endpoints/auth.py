from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.config import get_settings
from app.core.email import send_password_reset_email
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    Token,
)
from app.schemas.user import PasswordChange, UserCreate, UserResponse
from app.services.audit import create_audit_log, log_model_change
from app.services.password_reset import (
    create_reset_token,
    mark_token_used,
    validate_reset_token,
)

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


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate a user with email and password. Returns access and refresh tokens.",
    responses={
        200: {"description": "Login successful", "model": Token},
        401: {"description": "Invalid credentials"},
        400: {"description": "Inactive user account"},
        429: {"description": "Rate limit exceeded"},
    },
)
@conditional_rate_limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Authenticate user and return JWT tokens.

    Args:
        request: FastAPI request object
        login_data: Login credentials (email and password)
        db: Database session

    Returns:
        Token object containing access_token, refresh_token, and token_type

    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 400 if user account is inactive
    """
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none() if result else None

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

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

    # Log successful login
    await create_audit_log(
        db=db,
        action=AuditAction.LOGIN,
        table_name="users",
        record_id=str(user.id),
        user_id=user.id,
        user_email=user.email,
        request=request,
        description=f"User logged in: {user.email}",
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Exchange a refresh token for a new access token and refresh token pair.",
    responses={
        200: {"description": "Tokens refreshed successfully", "model": Token},
        401: {"description": "Invalid refresh token"},
        429: {"description": "Rate limit exceeded"},
    },
)
@conditional_rate_limit("10/minute")
async def refresh_token(
    request: Request,
    refresh_data: RefreshRequest,
) -> Any:
    """Refresh JWT tokens using a valid refresh token.

    Args:
        request: FastAPI request object
        refresh_data: Refresh token data

    Returns:
        Token object containing new access_token and refresh_token

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
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


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User registration",
    description="Register a new user account with email and password.",
    responses={
        201: {"description": "User registered successfully", "model": UserResponse},
        400: {"description": "Email already registered or invalid data"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
    },
)
@conditional_rate_limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Register a new user.

    Creates a new user account with the provided email and password.
    Password is hashed before storage. Returns the created user without tokens.

    Args:
        request: FastAPI request object
        user_data: User registration data (email, password, optional first/last name)
        db: Database session

    Returns:
        UserResponse with created user data

    Raises:
        HTTPException: 400 if email already exists
        HTTPException: 422 if validation fails
    """
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

    # Log user registration
    await log_model_change(
        db=db,
        action=AuditAction.CREATE,
        model_instance=user,
        user_id=user.id,
        user_email=user.email,
        request=request,
        description=f"User registered: {user.email}",
    )

    logger.info(f"User registered: {user.email}", extra={"user_id": user.id})
    return user


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Change the current user's password. Requires current password for verification.",
    responses={
        204: {"description": "Password changed successfully"},
        400: {"description": "Current password is incorrect"},
        401: {"description": "Not authenticated"},
        404: {"description": "User not found"},
    },
)
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Change user password.

    Requires the current password for verification. The new password
    must meet minimum length requirements.

    Args:
        password_data: Password change data (current and new password)
        current_user: Current authenticated user from token
        db: Database session

    Raises:
        HTTPException: 400 if current password is incorrect
        HTTPException: 401 if not authenticated
        HTTPException: 404 if user not found
    """
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


@router.post(
    "/forgot-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Request password reset",
    description="Request a password reset email. Always returns 204 to prevent email enumeration.",
    responses={
        204: {"description": "Reset email sent (or user not found - indistinguishable)"},
        429: {"description": "Rate limit exceeded (max 3 per hour)"},
    },
)
@conditional_rate_limit("3/hour")
async def forgot_password(
    request: Request,
    request_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Request password reset email.

    Sends a password reset email to the provided email address if it exists.
    Always returns 204 status to prevent email enumeration attacks.
    The reset token is valid for 24 hours.

    Args:
        request: FastAPI request object
        request_data: Forgot password request data (email)
        db: Database session

    Note:
        Returns 204 even if email doesn't exist to prevent user enumeration
        Rate limited to 3 requests per hour per IP
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


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset password with token",
    description="Reset user password using a valid reset token from email.",
    responses={
        204: {"description": "Password reset successfully"},
        400: {"description": "Invalid or expired token"},
    },
)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Reset password with token.

    Resets the user's password using a valid reset token received via email.
    The token must be valid and not expired (24 hour expiry).
    After reset, the token is marked as used and cannot be reused.

    Args:
        reset_data: Reset password data (token and new password)
        db: Database session

    Raises:
        HTTPException: 400 if token is invalid or expired

    Note:
        The new password must meet minimum length requirements
    """
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
