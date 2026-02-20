from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.permissions import check_resource_permission
from app.models.audit_log import AuditAction
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.audit import create_audit_log, log_model_change
from app.services.rbac import check_permission, get_all_subordinate_ids, get_user_permissions

router = APIRouter(
    tags=["tasks"],
    responses={404: {"description": "Task not found"}},
)


@router.get(
    "/",
    response_model=List[TaskResponse],
    summary="List tasks",
    description="Get a paginated list of tasks based on user's permissions.",
)
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get paginated list of tasks based on permissions."""
    # Check read permission
    perms = await get_user_permissions(db, current_user["id"], "tasks")
    read_scope = perms.get("read")

    if read_scope is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to read tasks",
        )

    # Build query based on scope
    if read_scope == "all":
        query = select(Task).where(Task.deleted_at.is_(None))
    elif read_scope == "subordinates":
        subordinate_ids = await get_all_subordinate_ids(db, current_user["id"])
        subordinate_ids.append(current_user["id"])
        query = select(Task).where(
            Task.user_id.in_(subordinate_ids),
            Task.deleted_at.is_(None)
        )
    else:  # "own"
        query = select(Task).where(
            Task.user_id == current_user["id"],
            Task.deleted_at.is_(None)
        )

    result = await db.execute(query.offset(skip).limit(limit))
    tasks = result.scalars().all()
    return tasks


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    task_data: TaskCreate,
    request: Request,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new task."""
    # Check create permission
    can_create = await check_permission(
        db, current_user["id"], "tasks", "create"
    )
    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to create tasks",
        )

    task = Task(**task_data.model_dump(), user_id=current_user["id"])
    db.add(task)
    await db.commit()
    await db.refresh(task)

    await log_model_change(
        db=db,
        action=AuditAction.CREATE,
        model_instance=task,
        user_id=current_user["id"],
        user_email=current_user.get("email"),
        request=request,
        description=f"Created task: {task.title}",
    )

    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get task by ID."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check permission for this specific task
    can_read = await check_resource_permission(
        db, current_user["id"], "tasks", "read", task.user_id
    )
    if not can_read:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to read this task",
        )

    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    request: Request,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update task by ID."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check permission for this specific task
    can_update = await check_resource_permission(
        db, current_user["id"], "tasks", "update", task.user_id
    )
    if not can_update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to update this task",
        )

    old_values = {
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
    }

    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    await log_model_change(
        db=db,
        action=AuditAction.UPDATE,
        model_instance=task,
        user_id=current_user["id"],
        user_email=current_user.get("email"),
        request=request,
        old_values=old_values,
        description=f"Updated task: {task.title}",
    )

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    request: Request,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete task by ID."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check permission for this specific task
    can_delete = await check_resource_permission(
        db, current_user["id"], "tasks", "delete", task.user_id
    )
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to delete this task",
        )

    old_values = {
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
    }

    await create_audit_log(
        db=db,
        action=AuditAction.DELETE,
        table_name="tasks",
        record_id=str(task.id),
        user_id=current_user["id"],
        user_email=current_user.get("email"),
        request=request,
        old_values=old_values,
        description=f"Deleted task: {task.title}",
    )

    task.soft_delete()
    await db.commit()
