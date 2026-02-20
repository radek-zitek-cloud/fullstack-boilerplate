from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class TrashItemResponse(BaseModel):
    """Schema for trash item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    name: str
    deleted_at: datetime
    deleted_by: Optional[str] = None
    data: dict[str, Any]


class TrashListResponse(BaseModel):
    """Schema for paginated trash list."""

    items: list[TrashItemResponse]
    total: int
    skip: int
    limit: int


class TrashActionResponse(BaseModel):
    """Schema for trash action response (restore/delete)."""

    success: bool
    message: str


class EmptyTrashResponse(BaseModel):
    """Schema for empty trash response."""

    success: bool
    message: str
    deleted: dict[str, int]  # counts by type
