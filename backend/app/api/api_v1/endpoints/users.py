from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.sanitization import sanitize_html, sanitize_text
from app.models.user import User
from app.schemas.user import ProfileUpdate, UserResponse


# Fields that should be sanitized
HTML_FIELDS = {"note"}
TEXT_FIELDS = {"first_name", "last_name"}

router = APIRouter(
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the profile information of the currently authenticated user.",
    responses={
        200: {"description": "User profile retrieved successfully", "model": UserResponse},
        401: {"description": "Not authenticated"},
        404: {"description": "User not found"},
    },
)
async def get_me(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get current authenticated user's profile.

    Retrieves the complete profile information for the currently authenticated user,
    including personal details, permissions, and timestamps.

    Args:
        current_user: Current authenticated user from JWT token
        db: Database session

    Returns:
        UserResponse with user profile data

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 404 if user not found (rare, user deleted after token issued)
    """
    result = await db.execute(
        select(User).where(User.id == current_user["id"], User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update the profile of the currently authenticated user.",
    responses={
        200: {"description": "User profile updated successfully", "model": UserResponse},
        401: {"description": "Not authenticated"},
        404: {"description": "User not found"},
        422: {"description": "Validation error"},
    },
)
async def update_me(
    profile_data: ProfileUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update current authenticated user's profile.

    Updates user profile fields. Only provided fields are updated (partial update).
    Input is sanitized to prevent XSS attacks:
    - first_name, last_name: HTML tags stripped
    - note: HTML sanitized

    Args:
        profile_data: Profile update data (only include fields to update)
        current_user: Current authenticated user from JWT token
        db: Database session

    Returns:
        UserResponse with updated user data

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 404 if user not found
        HTTPException: 422 if validation fails
    """
    result = await db.execute(
        select(User).where(User.id == current_user["id"], User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = profile_data.model_dump(exclude_unset=True)

    # Sanitize input fields
    for field, value in update_data.items():
        if field in HTML_FIELDS:
            value = sanitize_html(value)
        elif field in TEXT_FIELDS:
            value = sanitize_text(value)
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Get a specific user by ID. Users can only access their own profile, admins can access any.",
    responses={
        200: {"description": "User found", "model": UserResponse},
        401: {"description": "Not authenticated"},
        403: {"description": "Not enough permissions (can only access own profile)"},
        404: {"description": "User not found"},
    },
)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get user by ID.

    Retrieves user information by ID. Regular users can only access their own profile.
    Admin users can access any user's profile.

    Args:
        user_id: ID of the user to retrieve
        current_user: Current authenticated user from JWT token
        db: Database session

    Returns:
        UserResponse with user data

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if trying to access another user's profile (non-admin)
        HTTPException: 404 if user not found
    """
    # Only allow users to get their own info or admin can get anyone
    if current_user["id"] != user_id and not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List all users",
    description="Get a paginated list of all users. Admin access only.",
    responses={
        200: {"description": "List of users", "model": List[UserResponse]},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
    },
)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all users (Admin only).

    Retrieves a paginated list of all registered users.
    This endpoint is restricted to admin users only.

    Args:
        skip: Number of users to skip (for pagination)
        limit: Maximum number of users to return (default: 100, max: 1000)
        current_user: Current authenticated user from JWT token
        db: Database session

    Returns:
        List of UserResponse objects

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not an admin

    Note:
        Use skip and limit for pagination. Maximum limit is 1000.
    """
    # Only admin can list all users
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    result = await db.execute(
        select(User).where(User.deleted_at.is_(None)).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users
