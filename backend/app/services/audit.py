from datetime import datetime
from typing import Any, Optional

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.audit_log import AuditAction, AuditLog

logger = get_logger(__name__)


async def create_audit_log(
    db: AsyncSession,
    action: AuditAction,
    table_name: str,
    record_id: Optional[str] = None,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    old_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    request: Optional[Request] = None,
    description: Optional[str] = None,
) -> AuditLog:
    """Create an audit log entry.

    Args:
        db: Database session
        action: Type of action performed (create, update, delete, etc.)
        table_name: Name of the affected table
        record_id: ID of the affected record
        user_id: ID of the user who performed the action
        user_email: Email of the user who performed the action
        old_values: Previous values (for updates/deletes)
        new_values: New values (for creates/updates)
        request: FastAPI request object for extracting IP/user agent
        description: Human-readable description

    Returns:
        Created audit log entry
    """
    # Extract request info if available
    ip_address = None
    user_agent = None
    endpoint = None
    method = None

    if request:
        # Get client IP (handle proxies)
        if request.headers.get("X-Forwarded-For"):
            ip_address = request.headers.get("X-Forwarded-For").split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None

        user_agent = request.headers.get("User-Agent")
        endpoint = str(request.url.path)
        method = request.method

    audit_log = AuditLog(
        user_id=user_id,
        user_email=user_email,
        action=action.value,
        table_name=table_name,
        record_id=record_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
        description=description,
    )

    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)

    logger.debug(
        f"Audit log created: {action.value} on {table_name}",
        extra={
            "audit_id": audit_log.id,
            "user_id": user_id,
            "action": action.value,
            "table": table_name,
        },
    )

    return audit_log


async def log_model_change(
    db: AsyncSession,
    action: AuditAction,
    model_instance: Any,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    request: Optional[Request] = None,
    old_values: Optional[dict[str, Any]] = None,
    description: Optional[str] = None,
) -> AuditLog:
    """Log a model change with automatic table/ID extraction.

    Args:
        db: Database session
        action: Type of action
        model_instance: SQLAlchemy model instance
        user_id: ID of the user
        user_email: Email of the user
        request: FastAPI request object
        old_values: Previous values for updates
        description: Description of the change

    Returns:
        Created audit log entry
    """
    table_name = model_instance.__tablename__
    record_id = str(getattr(model_instance, "id", None))

    # Extract current values for create/update
    new_values = None
    if action in (AuditAction.CREATE, AuditAction.UPDATE):
        new_values = _model_to_dict(model_instance)

    return await create_audit_log(
        db=db,
        action=action,
        table_name=table_name,
        record_id=record_id,
        user_id=user_id,
        user_email=user_email,
        old_values=old_values,
        new_values=new_values,
        request=request,
        description=description,
    )


async def get_audit_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    table_name: Optional[str] = None,
    action: Optional[str] = None,
    record_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[AuditLog]:
    """Get audit logs with optional filtering.

    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum records to return
        user_id: Filter by user ID
        table_name: Filter by table name
        action: Filter by action type
        record_id: Filter by record ID
        start_date: Filter by start date (inclusive)
        end_date: Filter by end date (inclusive)

    Returns:
        List of audit log entries
    """
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

    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_audit_log_by_id(db: AsyncSession, audit_id: int) -> Optional[AuditLog]:
    """Get a single audit log by ID.

    Args:
        db: Database session
        audit_id: Audit log ID

    Returns:
        Audit log entry or None if not found
    """
    result = await db.execute(select(AuditLog).where(AuditLog.id == audit_id))
    return result.scalar_one_or_none()


def _model_to_dict(model_instance: Any) -> dict[str, Any]:
    """Convert SQLAlchemy model instance to dictionary.

    Args:
        model_instance: SQLAlchemy model instance

    Returns:
        Dictionary representation of the model
    """
    result = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        # Convert datetime to ISO format for JSON serialization
        if isinstance(value, datetime):
            value = value.isoformat()
        result[column.name] = value
    return result
