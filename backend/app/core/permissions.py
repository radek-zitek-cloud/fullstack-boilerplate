"""Permission-based dependency injection for FastAPI.

This module provides FastAPI dependencies for checking permissions
in API endpoints using the RBAC system.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.logging import get_logger
from app.services.rbac import check_permission

logger = get_logger(__name__)


def require_permission(
    component: str,
    action: str,
):
    """Create a FastAPI dependency that checks for a specific permission.

    Args:
        component: Component name (e.g., "tasks", "users")
        action: Action to check ("create", "read", "update", "delete")

    Returns:
        FastAPI dependency function

    Example:
        @router.get("/{task_id}")
        async def get_task(
            task_id: int,
            current_user: dict = Depends(require_permission("tasks", "read")),
            db: AsyncSession = Depends(get_db)
        ):
            # User has read permission on tasks
            ...
    """

    async def permission_checker(
        current_user: dict = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        has_perm = await check_permission(
            db=db,
            user_id=current_user["id"],
            component=component,
            action=action,
            resource_owner_id=None,  # General permission check
        )

        if not has_perm:
            logger.warning(
                f"Permission denied: user={current_user['id']}, "
                f"component={component}, action={action}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions for {action} on {component}",
            )

        return current_user

    return permission_checker


async def check_resource_permission(
    db: AsyncSession,
    user_id: int,
    component: str,
    action: str,
    resource_owner_id: int,
) -> bool:
    """Check permission for a specific resource.

    Use this when you need to check permission for a specific resource
    (e.g., can user update this specific task).

    Args:
        db: Database session
        user_id: User ID performing the action
        component: Component name
        action: Action to check
        resource_owner_id: Owner of the resource being accessed

    Returns:
        True if allowed, False otherwise

    Example:
        task = await get_task(db, task_id)
        can_update = await check_resource_permission(
            db, current_user["id"], "tasks", "update", task.user_id
        )
        if not can_update:
            raise HTTPException(403, "Cannot update this task")
    """
    return await check_permission(
        db=db,
        user_id=user_id,
        component=component,
        action=action,
        resource_owner_id=resource_owner_id,
    )
