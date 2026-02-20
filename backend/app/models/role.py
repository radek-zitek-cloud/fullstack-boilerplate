from typing import TYPE_CHECKING, Dict, Optional

from sqlalchemy import JSON, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user_role import UserRole


class Role(Base, TimestampMixin):
    """Role model for component-scoped permissions.

    Roles define what actions users can perform on specific components.
    Permissions are stored as JSON with action: scope mapping.

    Example:
        {
            "component": "tasks",
            "name": "Manager",
            "permissions": {
                "create": "own",
                "read": "subordinates",
                "update": "subordinates",
                "delete": None
            }
        }

    Scopes:
        - "own": User can only act on their own resources
        - "subordinates": User can act on resources of their subordinates
        - "all": User can act on any resource
        - None: Permission denied
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    component: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Permissions stored as JSON: {"create": "own", "read": "all", "update": null, "delete": null}
    # Actions: create, read, update, delete
    # Scopes: own, subordinates, all, null (deny)
    permissions: Mapped[Dict[str, Optional[str]]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Relationships
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="role", lazy="selectin", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("component", "name", name="uix_role_component_name"),)

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, component={self.component}, name={self.name})>"
