"""Pydantic schemas for Role-Based Access Control (RBAC)."""

from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class RoleBase(BaseModel):
    """Base schema for roles."""

    component: str
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a role."""

    permissions: Dict[str, Optional[str]]

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v):
        """Validate permission scopes."""
        valid_actions = {"create", "read", "update", "delete"}
        valid_scopes = {"own", "subordinates", "all", None}

        for action, scope in v.items():
            if action not in valid_actions:
                raise ValueError(f"Invalid action: {action}. Must be one of {valid_actions}")
            if scope not in valid_scopes:
                raise ValueError(f"Invalid scope: {scope}. Must be one of {valid_scopes}")

        return v


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    description: Optional[str] = None
    permissions: Optional[Dict[str, Optional[str]]] = None

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, v):
        """Validate permission scopes."""
        if v is None:
            return v

        valid_actions = {"create", "read", "update", "delete"}
        valid_scopes = {"own", "subordinates", "all", None}

        for action, scope in v.items():
            if action not in valid_actions:
                raise ValueError(f"Invalid action: {action}. Must be one of {valid_actions}")
            if scope not in valid_scopes:
                raise ValueError(f"Invalid scope: {scope}. Must be one of {valid_scopes}")

        return v


class RoleResponse(RoleBase):
    """Schema for role response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    permissions: Dict[str, Optional[str]]


class UserRoleAssignment(BaseModel):
    """Schema for assigning a role to a user."""

    role_id: int


class UserRolesResponse(BaseModel):
    """Schema for user roles response."""

    user_id: int
    user_email: str
    user_full_name: str
    roles: list[RoleResponse]
