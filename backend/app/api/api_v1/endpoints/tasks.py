from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(
    tags=["tasks"],
    responses={404: {"description": "Task not found"}},
)


@router.get(
    "/",
    response_model=List[TaskResponse],
    summary="List tasks",
    description="Get a paginated list of tasks for the current user.",
    responses={
        200: {"description": "List of tasks", "model": List[TaskResponse]},
        401: {"description": "Not authenticated"},
    },
)
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get paginated list of tasks for current user.
    
    Retrieves tasks belonging to the authenticated user with pagination support.
    Tasks are sorted by creation date (newest first).
    
    Args:
        skip: Number of tasks to skip (for pagination)
        limit: Maximum number of tasks to return (default: 100, max: 1000)
        current_user: Current authenticated user from JWT token
        db: Database session
        
    Returns:
        List of TaskResponse objects
        
    Raises:
        HTTPException: 401 if not authenticated
    """
    result = await db.execute(
        select(Task).where(Task.user_id == current_user["id"]).offset(skip).limit(limit)
    )
    tasks = result.scalars().all()
    return tasks


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    description="Create a new task for the current user.",
    responses={
        201: {"description": "Task created successfully", "model": TaskResponse},
        401: {"description": "Not authenticated"},
        422: {"description": "Validation error"},
    },
)
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new task.
    
    Creates a new task belonging to the authenticated user.
    Tasks can have a title, description, and completion status.
    
    Args:
        task_data: Task creation data (title, description, completed)
        current_user: Current authenticated user from JWT token
        db: Database session
        
    Returns:
        TaskResponse with created task data
        
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 422 if validation fails
    """
    task = Task(**task_data.model_dump(), user_id=current_user["id"])
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task",
    description="Get a specific task by ID. Users can only access their own tasks.",
    responses={
        200: {"description": "Task found", "model": TaskResponse},
        401: {"description": "Not authenticated"},
        404: {"description": "Task not found"},
    },
)
async def get_task(
    task_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get task by ID.
    
    Retrieves a specific task by its ID. Users can only access tasks
    that belong to them.
    
    Args:
        task_id: ID of the task to retrieve
        current_user: Current authenticated user from JWT token
        db: Database session
        
    Returns:
        TaskResponse with task data
        
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 404 if task not found or doesn't belong to user
    """
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user["id"])
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update a specific task. Only provided fields are updated. Users can only update their own tasks.",
    responses={
        200: {"description": "Task updated successfully", "model": TaskResponse},
        401: {"description": "Not authenticated"},
        404: {"description": "Task not found"},
        422: {"description": "Validation error"},
    },
)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update task by ID.
    
    Updates a specific task. Only provided fields are updated (partial update).
    Users can only update tasks that belong to them.
    
    Args:
        task_id: ID of the task to update
        task_data: Task update data (only include fields to update)
        current_user: Current authenticated user from JWT token
        db: Database session
        
    Returns:
        TaskResponse with updated task data
        
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 404 if task not found
        HTTPException: 422 if validation fails
    """
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user["id"])
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Delete a specific task. Users can only delete their own tasks.",
    responses={
        204: {"description": "Task deleted successfully"},
        401: {"description": "Not authenticated"},
        404: {"description": "Task not found"},
    },
)
async def delete_task(
    task_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete task by ID.
    
    Permanently deletes a specific task. Users can only delete tasks
    that belong to them. This action cannot be undone.
    
    Args:
        task_id: ID of the task to delete
        current_user: Current authenticated user from JWT token
        db: Database session
        
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 404 if task not found
    """
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == current_user["id"])
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    await db.delete(task)
    await db.commit()
