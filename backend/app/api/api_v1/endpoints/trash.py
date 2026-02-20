from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db
from app.schemas.trash import (
    EmptyTrashResponse,
    TrashActionResponse,
    TrashItemResponse,
    TrashListResponse,
)
from app.services.trash import empty_trash, get_trash_items, permanently_delete, restore_item

router = APIRouter(
    prefix="/trash",
    tags=["trash"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=TrashListResponse,
    summary="List trash items",
    description="Get all soft-deleted items. Admin access only.",
    responses={
        200: {"description": "List of trash items", "model": TrashListResponse},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
    },
)
async def list_trash(
    item_type: Optional[str] = Query(
        None, description="Filter by type: 'user', 'task', or None for all"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get all soft-deleted items from trash.

    Retrieves a paginated list of soft-deleted users and/or tasks.
    This endpoint is restricted to admin users only.

    Args:
        item_type: Filter by type ('user', 'task', or None for all)
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        TrashListResponse with items and pagination info

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not an admin
    """
    items = await get_trash_items(db, item_type=item_type, skip=skip, limit=limit)

    # Get total count (simplified - actual count would need separate query)
    all_items = await get_trash_items(db, item_type=item_type, skip=0, limit=10000)
    total = len(all_items)

    return TrashListResponse(
        items=[
            TrashItemResponse(
                id=item.id,
                type=item.type,
                name=item.name,
                deleted_at=item.deleted_at,
                deleted_by=item.deleted_by,
                data=item.data,
            )
            for item in items
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/restore/{item_type}/{item_id}",
    response_model=TrashActionResponse,
    summary="Restore item from trash",
    description="Restore a soft-deleted item. Admin access only.",
    responses={
        200: {"description": "Item restored successfully", "model": TrashActionResponse},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        404: {"description": "Item not found in trash"},
    },
)
async def restore_trash_item(
    item_type: str,
    item_id: int,
    request: Request,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Restore a soft-deleted item from trash.

    Args:
        item_type: Type of item ('user' or 'task')
        item_id: ID of the item to restore
        request: FastAPI request object
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        TrashActionResponse indicating success/failure

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 404 if item not found in trash
    """
    success = await restore_item(
        db=db,
        item_type=item_type,
        item_id=item_id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{item_type} not found in trash",
        )

    return TrashActionResponse(
        success=True,
        message=f"{item_type} restored successfully",
    )


@router.delete(
    "/{item_type}/{item_id}",
    response_model=TrashActionResponse,
    summary="Permanently delete item",
    description="Permanently delete an item from trash. This cannot be undone. Admin access only.",
    responses={
        200: {"description": "Item permanently deleted", "model": TrashActionResponse},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        404: {"description": "Item not found in trash"},
    },
)
async def delete_trash_item(
    item_type: str,
    item_id: int,
    request: Request,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Permanently delete an item from trash.

    WARNING: This action cannot be undone.

    Args:
        item_type: Type of item ('user' or 'task')
        item_id: ID of the item to delete
        request: FastAPI request object
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        TrashActionResponse indicating success/failure

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 404 if item not found in trash
    """
    success = await permanently_delete(
        db=db,
        item_type=item_type,
        item_id=item_id,
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{item_type} not found in trash",
        )

    return TrashActionResponse(
        success=True,
        message=f"{item_type} permanently deleted",
    )


@router.delete(
    "/",
    response_model=EmptyTrashResponse,
    summary="Empty trash",
    description="Permanently delete all items in trash. This cannot be undone. Admin access only.",
    responses={
        200: {"description": "Trash emptied successfully", "model": EmptyTrashResponse},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
    },
)
async def empty_trash_endpoint(
    request: Request,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Permanently delete all items in trash.

    WARNING: This action cannot be undone. All soft-deleted users and tasks
    will be permanently removed from the database.

    Args:
        request: FastAPI request object
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        EmptyTrashResponse with counts of deleted items

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not an admin
    """
    result = await empty_trash(
        db=db,
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
    )

    total_deleted = sum(result.values())

    return EmptyTrashResponse(
        success=True,
        message=f"Trash emptied successfully. {total_deleted} items permanently deleted.",
        deleted=result,
    )
