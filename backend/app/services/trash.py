"""Trash/Recycle bin service for soft deleted records.

Provides functionality to view, restore, and permanently delete soft-deleted records.
All operations are audited for compliance.
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.audit_log import AuditAction
from app.models.task import Task
from app.models.user import User
from app.services.audit import create_audit_log

logger = get_logger(__name__)


class TrashItem:
    """Represents an item in the trash."""

    def __init__(
        self,
        id: int,
        type: str,
        name: str,
        deleted_at: datetime,
        deleted_by: Optional[str],
        data: dict[str, Any],
    ):
        self.id = id
        self.type = type
        self.name = name
        self.deleted_at = deleted_at
        self.deleted_by = deleted_by
        self.data = data


async def get_trash_items(
    db: AsyncSession,
    item_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[TrashItem]:
    """Get all soft-deleted items.

    Args:
        db: Database session
        item_type: Filter by type ('user', 'task', or None for all)
        skip: Pagination offset
        limit: Max items to return

    Returns:
        List of TrashItem objects
    """
    items: list[TrashItem] = []

    # Get deleted users
    if item_type is None or item_type == "user":
        result = await db.execute(
            select(User)
            .where(User.deleted_at.isnot(None))
            .order_by(User.deleted_at.desc())
            .offset(skip if item_type == "user" else 0)
            .limit(limit if item_type == "user" else limit // 2)
        )
        users = result.scalars().all()

        for user in users:
            items.append(
                TrashItem(
                    id=user.id,
                    type="user",
                    name=user.email,
                    deleted_at=user.deleted_at,
                    deleted_by=None,  # Could lookup from audit log
                    data={
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "is_admin": user.is_admin,
                        "is_active": user.is_active,
                    },
                )
            )

    # Get deleted tasks
    if item_type is None or item_type == "task":
        result = await db.execute(
            select(Task)
            .where(Task.deleted_at.isnot(None))
            .order_by(Task.deleted_at.desc())
            .offset(skip if item_type == "task" else 0)
            .limit(limit if item_type == "task" else limit // 2)
        )
        tasks = result.scalars().all()

        for task in tasks:
            items.append(
                TrashItem(
                    id=task.id,
                    type="task",
                    name=task.title,
                    deleted_at=task.deleted_at,
                    deleted_by=None,
                    data={
                        "title": task.title,
                        "status": task.status.value,
                        "priority": task.priority.value,
                        "user_id": task.user_id,
                    },
                )
            )

    # Sort by deleted_at descending
    items.sort(key=lambda x: x.deleted_at, reverse=True)
    return items[skip : skip + limit]


async def restore_item(
    db: AsyncSession,
    item_type: str,
    item_id: int,
    user_id: int,
    user_email: str,
    request: Optional[Request] = None,
) -> bool:
    """Restore a soft-deleted item.

    Args:
        db: Database session
        item_type: Type of item ('user' or 'task')
        item_id: ID of item to restore
        user_id: ID of user performing restore
        user_email: Email of user performing restore
        request: FastAPI request for audit context

    Returns:
        True if restored, False if not found
    """
    if item_type == "user":
        result = await db.execute(
            select(User).where(User.id == item_id, User.deleted_at.isnot(None))
        )
        user = result.scalar_one_or_none()

        if not user:
            return False

        # Restore the user
        user.restore()
        await db.commit()

        # Audit the restoration
        await create_audit_log(
            db=db,
            action=AuditAction.UPDATE,
            table_name="users",
            record_id=str(user.id),
            user_id=user_id,
            user_email=user_email,
            request=request,
            description=f"Restored user from trash: {user.email}",
        )

        logger.info(f"User restored from trash: {user.email}", extra={"user_id": user.id})
        return True

    elif item_type == "task":
        result = await db.execute(
            select(Task).where(Task.id == item_id, Task.deleted_at.isnot(None))
        )
        task = result.scalar_one_or_none()

        if not task:
            return False

        # Restore the task
        task.restore()
        await db.commit()

        # Audit the restoration
        await create_audit_log(
            db=db,
            action=AuditAction.UPDATE,
            table_name="tasks",
            record_id=str(task.id),
            user_id=user_id,
            user_email=user_email,
            request=request,
            description=f"Restored task from trash: {task.title}",
        )

        logger.info(f"Task restored from trash: {task.title}", extra={"task_id": task.id})
        return True

    return False


async def permanently_delete(
    db: AsyncSession,
    item_type: str,
    item_id: int,
    user_id: int,
    user_email: str,
    request: Optional[Request] = None,
) -> bool:
    """Permanently delete an item from trash.

    WARNING: This action cannot be undone.

    Args:
        db: Database session
        item_type: Type of item ('user' or 'task')
        item_id: ID of item to delete
        user_id: ID of user performing deletion
        user_email: Email of user performing deletion
        request: FastAPI request for audit context

    Returns:
        True if deleted, False if not found
    """
    if item_type == "user":
        result = await db.execute(
            select(User).where(User.id == item_id, User.deleted_at.isnot(None))
        )
        user = result.scalar_one_or_none()

        if not user:
            return False

        # Store info for audit
        user_email_deleted = user.email

        # Permanently delete
        await db.delete(user)
        await db.commit()

        # Audit permanent deletion
        await create_audit_log(
            db=db,
            action=AuditAction.DELETE,
            table_name="users",
            record_id=str(item_id),
            user_id=user_id,
            user_email=user_email,
            request=request,
            description=f"Permanently deleted user from trash: {user_email_deleted}",
        )

        logger.info(
            f"User permanently deleted from trash: {user_email_deleted}",
            extra={"user_id": item_id},
        )
        return True

    elif item_type == "task":
        result = await db.execute(
            select(Task).where(Task.id == item_id, Task.deleted_at.isnot(None))
        )
        task = result.scalar_one_or_none()

        if not task:
            return False

        # Store info for audit
        task_title = task.title

        # Permanently delete
        await db.delete(task)
        await db.commit()

        # Audit permanent deletion
        await create_audit_log(
            db=db,
            action=AuditAction.DELETE,
            table_name="tasks",
            record_id=str(item_id),
            user_id=user_id,
            user_email=user_email,
            request=request,
            description=f"Permanently deleted task from trash: {task_title}",
        )

        logger.info(
            f"Task permanently deleted from trash: {task_title}",
            extra={"task_id": item_id},
        )
        return True

    return False


async def empty_trash(
    db: AsyncSession,
    user_id: int,
    user_email: str,
    request: Optional[Request] = None,
) -> dict[str, int]:
    """Permanently delete all items in trash.

    WARNING: This action cannot be undone.

    Args:
        db: Database session
        user_id: ID of user performing deletion
        user_email: Email of user performing deletion
        request: FastAPI request for audit context

    Returns:
        Dict with count of deleted items by type
    """
    # Get all deleted users
    result = await db.execute(select(User).where(User.deleted_at.isnot(None)))
    deleted_users = result.scalars().all()
    user_count = len(deleted_users)

    # Get all deleted tasks
    result = await db.execute(select(Task).where(Task.deleted_at.isnot(None)))
    deleted_tasks = result.scalars().all()
    task_count = len(deleted_tasks)

    # Delete all
    for user in deleted_users:
        await db.delete(user)
    for task in deleted_tasks:
        await db.delete(task)

    await db.commit()

    # Audit empty trash
    await create_audit_log(
        db=db,
        action=AuditAction.DELETE,
        table_name="trash",
        record_id=None,
        user_id=user_id,
        user_email=user_email,
        request=request,
        description=f"Emptied trash: {user_count} users, {task_count} tasks permanently deleted",
    )

    logger.info(f"Trash emptied: {user_count} users, {task_count} tasks deleted")

    return {"users": user_count, "tasks": task_count}
