from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    """Base schema for audit log entries."""

    action: str
    table_name: str
    record_id: Optional[str] = None
    description: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating audit log entries."""

    user_id: Optional[int] = None
    user_email: Optional[str] = None
    old_values: Optional[dict[str, Any]] = None
    new_values: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None


class AuditLogResponse(AuditLogBase):
    """Schema for audit log responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    old_values: Optional[dict[str, Any]] = None
    new_values: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list."""

    items: list[AuditLogResponse]
    total: int
    skip: int
    limit: int


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs."""

    user_id: Optional[int] = None
    table_name: Optional[str] = None
    action: Optional[str] = None
    record_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
