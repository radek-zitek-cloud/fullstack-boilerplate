from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db
from app.models.audit_log import AuditAction, AuditLog
from app.schemas.audit import AuditLogFilter, AuditLogListResponse, AuditLogResponse

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=AuditLogListResponse,
    summary="List audit logs",
    description="Get a paginated list of audit logs with optional filtering. Admin access only.",
    responses={
        200: {"description": "List of audit logs", "model": AuditLogListResponse},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
    },
)
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    table_name: Optional[str] = Query(
        None, description="Filter by table name (e.g., 'users', 'tasks')"
    ),
    action: Optional[str] = Query(
        None, description="Filter by action (create, update, delete, read, login, logout)"
    ),
    record_id: Optional[str] = Query(None, description="Filter by record ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO format)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get audit logs with filtering and pagination.

    Retrieves a paginated list of audit log entries with optional filters.
    This endpoint is restricted to admin users only.

    Args:
        user_id: Filter by user ID who performed the action
        table_name: Filter by affected table (e.g., 'users', 'tasks')
        action: Filter by action type (create, update, delete, read, login, logout)
        record_id: Filter by specific record ID
        start_date: Filter by start date (inclusive)
        end_date: Filter by end date (inclusive)
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        AuditLogListResponse with items and pagination info

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not an admin

    Example:
        GET /api/v1/audit?table_name=tasks&action=create&limit=50
    """
    # Build query
    query = select(AuditLog)

    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
    if table_name:
        query = query.where(AuditLog.table_name == table_name)
    if action:
        query = query.where(AuditLog.action == action)
    if record_id:
        query = query.where(AuditLog.record_id == record_id)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)

    # Get total count
    count_query = select(func.count(AuditLog.id))
    if user_id is not None:
        count_query = count_query.where(AuditLog.user_id == user_id)
    if table_name:
        count_query = count_query.where(AuditLog.table_name == table_name)
    if action:
        count_query = count_query.where(AuditLog.action == action)
    if record_id:
        count_query = count_query.where(AuditLog.record_id == record_id)
    if start_date:
        count_query = count_query.where(AuditLog.created_at >= start_date)
    if end_date:
        count_query = count_query.where(AuditLog.created_at <= end_date)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    logs = list(result.scalars().all())

    return AuditLogListResponse(
        items=logs,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{audit_id}",
    response_model=AuditLogResponse,
    summary="Get audit log by ID",
    description="Get detailed information about a specific audit log entry. Admin access only.",
    responses={
        200: {"description": "Audit log found", "model": AuditLogResponse},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        404: {"description": "Audit log not found"},
    },
)
async def get_audit_log(
    audit_id: int,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get a specific audit log by ID.

    Retrieves detailed information about a single audit log entry.
    This endpoint is restricted to admin users only.

    Args:
        audit_id: ID of the audit log entry
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        AuditLogResponse with audit log details

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 404 if audit log not found
    """
    result = await db.execute(select(AuditLog).where(AuditLog.id == audit_id))
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )

    return log


@router.get(
    "/tables/list",
    response_model=List[str],
    summary="List audited tables",
    description="Get a list of all table names that have audit log entries. Admin access only.",
    responses={
        200: {"description": "List of table names"},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
    },
)
async def get_audited_tables(
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get list of all audited table names.

    Returns a unique list of table names that have audit log entries.
    Useful for filtering audit logs by table.

    Args:
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        List of table names

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not an admin
    """
    result = await db.execute(select(AuditLog.table_name).distinct().order_by(AuditLog.table_name))
    tables = [row[0] for row in result.all()]
    return tables


@router.get(
    "/actions/list",
    response_model=List[str],
    summary="List audit actions",
    description="Get a list of all action types in audit logs. Admin access only.",
    responses={
        200: {"description": "List of action types"},
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
    },
)
async def get_audit_actions(
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get list of all audit action types.

    Returns a unique list of action types that exist in audit logs.
    Useful for filtering audit logs by action.

    Args:
        current_user: Current authenticated admin user
        db: Database session

    Returns:
        List of action types (create, update, delete, read, login, logout, etc.)

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not an admin
    """
    result = await db.execute(select(AuditLog.action).distinct().order_by(AuditLog.action))
    actions = [row[0] for row in result.all()]
    return actions
