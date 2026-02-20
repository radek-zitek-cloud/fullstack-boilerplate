"""Admin API endpoints for Role-Based Access Control (RBAC).

This module provides admin-only endpoints for:
- Managing roles (CRUD)
- Assigning roles to users
- Managing user hierarchy (manager relationships)
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_admin_user, get_db
from app.models.audit_log import AuditAction
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.role import (
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    UserRoleAssignment,
    UserRolesResponse,
)
from app.services.audit import create_audit_log
from app.services.rbac import get_all_subordinate_ids

router = APIRouter(
    prefix="/admin/rbac",
    tags=["admin-rbac"],
    responses={403: {"description": "Admin access required"}},
)


@router.get(
    "/roles",
    response_model=List[RoleResponse],
    summary="List all roles",
    description="Get all roles, optionally filtered by component. Admin only.",
)
async def list_roles(
    component: Optional[str] = None,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all roles.

    Args:
        component: Optional filter by component (e.g., "tasks")
        current_user: Current admin user
        db: Database session

    Returns:
        List of RoleResponse objects
    """
    query = select(Role)
    if component:
        query = query.where(Role.component == component)

    result = await db.execute(query.order_by(Role.component, Role.name))
    roles = result.scalars().all()
    return roles


@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create role",
    description="Create a new role with permissions. Admin only.",
)
async def create_role(
    role_data: RoleCreate,
    request: Request,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new role.

    Args:
        role_data: Role creation data
        request: FastAPI request object
        current_user: Current admin user
        db: Database session

    Returns:
        Created RoleResponse

    Raises:
        HTTPException: 400 if role already exists
    """
    # Check if role already exists for this component
    existing = await db.execute(
        select(Role).where(
            Role.component == role_data.component,
            Role.name == role_data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_data.name}' already exists for component '{role_data.component}'",
        )

    role = Role(
        component=role_data.component,
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions,
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)

    # Audit role creation
    await create_audit_log(
        db=db,
        action=AuditAction.CREATE,
        table_name="roles",
        record_id=str(role.id),
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
        description=f"Created role {role.component}:{role.name}",
    )

    return role


@router.get(
    "/roles/{role_id}",
    response_model=RoleResponse,
    summary="Get role by ID",
    description="Get details of a specific role. Admin only.",
)
async def get_role(
    role_id: int,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get role by ID.

    Args:
        role_id: Role ID
        current_user: Current admin user
        db: Database session

    Returns:
        RoleResponse

    Raises:
        HTTPException: 404 if role not found
    """
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    return role


@router.put(
    "/roles/{role_id}",
    response_model=RoleResponse,
    summary="Update role",
    description="Update role permissions. Admin only.",
)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    request: Request,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update role.

    Args:
        role_id: Role ID
        role_data: Role update data
        request: FastAPI request object
        current_user: Current admin user
        db: Database session

    Returns:
        Updated RoleResponse

    Raises:
        HTTPException: 404 if role not found
    """
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Store old values for audit
    old_values = {
        "description": role.description,
        "permissions": role.permissions,
    }

    # Update fields
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.permissions is not None:
        role.permissions = role_data.permissions

    await db.commit()
    await db.refresh(role)

    # Audit role update
    await create_audit_log(
        db=db,
        action=AuditAction.UPDATE,
        table_name="roles",
        record_id=str(role.id),
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
        old_values=old_values,
        new_values={
            "description": role.description,
            "permissions": role.permissions,
        },
        description=f"Updated role {role.component}:{role.name}",
    )

    return role


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete role",
    description="Delete a role. Admin only.",
)
async def delete_role(
    role_id: int,
    request: Request,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete role.

    Args:
        role_id: Role ID
        request: FastAPI request object
        current_user: Current admin user
        db: Database session

    Raises:
        HTTPException: 404 if role not found
    """
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Store info for audit
    role_info = f"{role.component}:{role.name}"

    await db.delete(role)
    await db.commit()

    # Audit role deletion
    await create_audit_log(
        db=db,
        action=AuditAction.DELETE,
        table_name="roles",
        record_id=str(role_id),
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
        description=f"Deleted role {role_info}",
    )


@router.get(
    "/permissions/{component}",
    summary="Get user permissions for component",
    description="Get the current user's permissions for a specific component. Available to all authenticated users.",
)
async def get_user_permissions_endpoint(
    component: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get permissions for the current user on a component.

    Args:
        component: Component name (e.g., "tasks")
        current_user: Current authenticated user
        db: Database session

    Returns:
        Dict with permissions for each action
    """
    from app.services.rbac import get_user_permissions

    permissions = await get_user_permissions(db, current_user["id"], component)
    return permissions


@router.get(
    "/users/{user_id}/roles",
    response_model=UserRolesResponse,
    summary="Get user roles",
    description="Get all roles assigned to a user. Admin only.",
)
async def get_user_roles(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get roles assigned to a user.

    Args:
        user_id: User ID
        current_user: Current admin user
        db: Database session

    Returns:
        UserRolesResponse with user info and roles

    Raises:
        HTTPException: 404 if user not found
    """
    # Check user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get user's roles with full role details
    query = (
        select(Role)
        .join(UserRole)
        .where(UserRole.user_id == user_id)
        .order_by(Role.component, Role.name)
    )
    result = await db.execute(query)
    roles = result.scalars().all()

    # Build full name from first_name and last_name
    user_full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email

    return UserRolesResponse(
        user_id=user_id,
        user_email=user.email,
        user_full_name=user_full_name,
        roles=[
            {
                "id": role.id,
                "component": role.component,
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions,
                "created_at": role.created_at,
            }
            for role in roles
        ],
    )


@router.post(
    "/users/{user_id}/roles",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Assign role to user",
    description="Assign a role to a user. Admin only.",
)
async def assign_role_to_user(
    user_id: int,
    assignment: UserRoleAssignment,
    request: Request,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Assign a role to a user.

    Args:
        user_id: User ID
        assignment: Role assignment data
        request: FastAPI request object
        current_user: Current admin user
        db: Database session

    Raises:
        HTTPException: 404 if user or role not found
        HTTPException: 400 if assignment already exists
    """
    # Check user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check role exists
    role_result = await db.execute(select(Role).where(Role.id == assignment.role_id))
    role = role_result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Check if assignment already exists
    existing = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == assignment.role_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already assigned to user",
        )

    # Create assignment
    user_role = UserRole(
        user_id=user_id,
        role_id=assignment.role_id,
    )
    db.add(user_role)
    await db.commit()

    # Audit role assignment
    await create_audit_log(
        db=db,
        action=AuditAction.CREATE,
        table_name="user_roles",
        record_id=f"{user_id}:{assignment.role_id}",
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
        description=f"Assigned role {role.component}:{role.name} to user {user.email}",
    )


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove role from user",
    description="Remove a role assignment from a user. Admin only.",
)
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    request: Request,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a role from a user.

    Args:
        user_id: User ID
        role_id: Role ID
        request: FastAPI request object
        current_user: Current admin user
        db: Database session

    Raises:
        HTTPException: 404 if user, role, or assignment not found
    """
    # Check user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check role exists
    role_result = await db.execute(select(Role).where(Role.id == role_id))
    role = role_result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    # Find and delete assignment
    assignment_result = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
    )
    user_role = assignment_result.scalar_one_or_none()

    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role assignment not found",
        )

    await db.delete(user_role)
    await db.commit()

    # Audit role removal
    await create_audit_log(
        db=db,
        action=AuditAction.DELETE,
        table_name="user_roles",
        record_id=f"{user_id}:{role_id}",
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
        description=f"Removed role {role.component}:{role.name} from user {user.email}",
    )


@router.put(
    "/users/{user_id}/manager",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update user manager",
    description="Assign or remove a manager for a user. Admin only.",
)
async def update_user_manager(
    user_id: int,
    request: Request,
    manager_id: Optional[int] = None,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Update a user's manager.

    Args:
        user_id: User ID
        manager_id: Manager's User ID (None to remove manager)
        request: FastAPI request object
        current_user: Current admin user
        db: Database session

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 400 if manager_id is same as user_id
    """
    # Check user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate manager assignment
    old_manager_id = user.manager_id
    if manager_id is not None:
        if manager_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User cannot be their own manager",
            )

        # Check manager exists
        manager_result = await db.execute(select(User).where(User.id == manager_id))
        manager = manager_result.scalar_one_or_none()

        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found",
            )

        # Check for circular dependency
        if manager_id:
            subordinate_ids = await get_all_subordinate_ids(db, user_id)
            if manager_id in subordinate_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot assign a subordinate as manager (circular dependency)",
                )

    # Update manager
    user.manager_id = manager_id
    await db.commit()

    # Audit manager change
    if manager_id != old_manager_id:
        if manager_id:
            new_manager_result = await db.execute(select(User).where(User.id == manager_id))
            new_manager = new_manager_result.scalar_one_or_none()
            description = f"Assigned manager {new_manager.email if new_manager else manager_id} to user {user.email}"
        else:
            description = f"Removed manager from user {user.email}"

        await create_audit_log(
            db=db,
            action=AuditAction.UPDATE,
            table_name="users",
            record_id=str(user_id),
            user_id=current_user["id"],
            user_email=current_user["email"],
            request=request,
            old_values={"manager_id": old_manager_id},
            new_values={"manager_id": manager_id},
            description=description,
        )


@router.get(
    "/hierarchy/{user_id}",
    summary="Get user hierarchy",
    description="Get the organizational hierarchy for a user (manager and all subordinates). Admin only.",
)
async def get_user_hierarchy(
    user_id: int,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get organizational hierarchy for a user.

    Args:
        user_id: User ID
        current_user: Current admin user
        db: Database session

    Returns:
        Dictionary with manager and subordinates info

    Raises:
        HTTPException: 404 if user not found
    """
    # Check user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get manager info
    manager_info = None
    if user.manager_id:
        manager_result = await db.execute(select(User).where(User.id == user.manager_id))
        manager = manager_result.scalar_one_or_none()
        if manager:
            manager_info = {
                "id": manager.id,
                "email": manager.email,
                "full_name": manager.full_name,
            }

    # Get all subordinates
    subordinate_ids = await get_all_subordinate_ids(db, user_id)
    subordinates = []
    if subordinate_ids:
        sub_result = await db.execute(
            select(User)
            .where(User.id.in_(subordinate_ids))
            .order_by(User.first_name, User.last_name)
        )
        subordinates = [
            {
                "id": sub.id,
                "email": sub.email,
                "full_name": sub.full_name,
            }
            for sub in sub_result.scalars().all()
        ]

    return {
        "user_id": user_id,
        "user_email": user.email,
        "user_full_name": user.full_name,
        "manager": manager_info,
        "subordinates": subordinates,
        "total_subordinates": len(subordinates),
    }


@router.get(
    "/users",
    summary="List all users with roles",
    description="Get all users with their assigned roles. Admin only.",
)
async def list_users_with_roles(
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all users with their roles.

    Args:
        current_user: Current admin user
        db: Database session

    Returns:
        List of users with their roles
    """
    # Get all non-deleted users
    result = await db.execute(
        select(User).where(User.deleted_at.is_(None)).order_by(User.first_name, User.last_name)
    )
    users = result.scalars().all()

    # Build response with roles for each user
    response = []
    for user in users:
        # Get user's roles
        role_query = select(Role).join(UserRole).where(UserRole.user_id == user.id)
        role_result = await db.execute(role_query)
        roles = role_result.scalars().all()

        response.append(
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "manager_id": user.manager_id,
                "roles": [
                    {
                        "id": role.id,
                        "component": role.component,
                        "name": role.name,
                    }
                    for role in roles
                ],
            }
        )

    return response


@router.post(
    "/users",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description="Create a new user. Admin only.",
)
async def create_user(
    request: Request,
    user_data: dict,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new user.

    Args:
        request: FastAPI request object
        user_data: User creation data
        current_user: Current admin user
        db: Database session

    Returns:
        Created user data

    Raises:
        HTTPException: 400 if email already exists
    """
    from app.core.security import get_password_hash

    # Validate required fields
    email = user_data.get("email")
    password = user_data.get("password")
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required",
        )

    # Check if email already exists (including soft-deleted)
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        is_active=user_data.get("is_active", True),
        is_admin=user_data.get("is_admin", False),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Audit user creation
    await create_audit_log(
        db=db,
        action=AuditAction.CREATE,
        table_name="users",
        record_id=str(user.id),
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
        description=f"Created user: {user.email}",
    )

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "full_name": user.full_name,
    }


@router.put(
    "/users/{user_id}",
    response_model=dict,
    summary="Update user",
    description="Update user details. Admin only.",
)
async def update_user(
    user_id: int,
    request: Request,
    user_data: dict,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update a user.

    Args:
        user_id: User ID
        request: FastAPI request object
        user_data: User update data
        current_user: Current admin user
        db: Database session

    Returns:
        Updated user data

    Raises:
        HTTPException: 404 if user not found
    """
    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Store old values for audit
    old_values = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
    }

    # Update fields
    if "email" in user_data:
        user.email = user_data["email"]
    if "first_name" in user_data:
        user.first_name = user_data["first_name"]
    if "last_name" in user_data:
        user.last_name = user_data["last_name"]
    if "is_active" in user_data:
        user.is_active = user_data["is_active"]
    if "is_admin" in user_data:
        user.is_admin = user_data["is_admin"]

    await db.commit()
    await db.refresh(user)

    # Audit user update
    await create_audit_log(
        db=db,
        action=AuditAction.UPDATE,
        table_name="users",
        record_id=str(user_id),
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
        old_values=old_values,
        new_values={
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
        },
        description=f"Updated user: {user.email}",
    )

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "full_name": user.full_name,
    }


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Soft delete a user. Admin only.",
)
async def delete_user(
    user_id: int,
    request: Request,
    current_user: dict = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft delete a user.

    Args:
        user_id: User ID
        request: FastAPI request object
        current_user: Current admin user
        db: Database session

    Raises:
        HTTPException: 404 if user not found
        HTTPException: 400 if trying to delete own account
    """
    from datetime import datetime, timezone

    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    result = await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Soft delete
    user.deleted_at = datetime.now(timezone.utc)
    await db.commit()

    # Audit user deletion
    await create_audit_log(
        db=db,
        action=AuditAction.DELETE,
        table_name="users",
        record_id=str(user_id),
        user_id=current_user["id"],
        user_email=current_user["email"],
        request=request,
        description=f"Deleted user: {user.email}",
    )
