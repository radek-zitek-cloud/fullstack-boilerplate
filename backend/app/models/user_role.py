from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.user import User


class UserRole(Base, TimestampMixin):
    """Association table linking users to their assigned roles.

    A user can have multiple roles, and a role can be assigned to multiple users.
    This allows for permission union - user gets the broadest permissions
    across all their assigned roles.

    Example:
        User A has roles:
        - Tasks: User (read: own, update: own)
        - Tasks: Manager (read: subordinates)
        Effective permission: read: subordinates (broadest scope)
    """

    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="roles", lazy="selectin")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles", lazy="selectin")

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
