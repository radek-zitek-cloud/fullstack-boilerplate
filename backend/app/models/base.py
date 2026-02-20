from datetime import datetime
from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, Boolean


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality to models.

    Records are marked as deleted by setting deleted_at timestamp.
    They are excluded from queries by default but can be restored.

    Example:
        class User(Base, SoftDeleteMixin):
            # User model with soft delete support
            pass

        # Query non-deleted records (default)
        db.query(User).all()

        # Include deleted records
        db.query(User).filter(User.deleted_at.isnot(None)).all()
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore soft deleted record."""
        self.deleted_at = None
