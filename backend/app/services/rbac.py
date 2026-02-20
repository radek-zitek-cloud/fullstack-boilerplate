"""Role-Based Access Control (RBAC) service.

This module provides comprehensive permission checking functionality
including hierarchical access control, permission unions across roles,
and component-scoped permissions.
"""

from typing import Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole

logger = get_logger(__name__)

# Priority order for permission scopes (higher = broader access)
SCOPE_PRIORITY = {"own": 1, "subordinates": 2, "all": 3}


async def get_user_roles(
    db: AsyncSession, user_id: int, component: Optional[str] = None
) -> List[Role]:
    """Get all roles assigned to a user.

    Args:
        db: Database session
        user_id: User ID
        component: Optional component filter (e.g., "tasks")

    Returns:
        List of Role objects
    """
    query = select(Role).join(UserRole).where(UserRole.user_id == user_id)

    if component:
        query = query.where(Role.component == component)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_permissions(
    db: AsyncSession, user_id: int, component: str
) -> Dict[str, Optional[str]]:
    """Get effective permissions for user on a component.

    Unions permissions across all roles, keeping the broadest scope
    for each action.

    Args:
        db: Database session
        user_id: User ID
        component: Component name (e.g., "tasks")

    Returns:
        Dict mapping action to scope ("own", "subordinates", "all", or None)
        Example: {"create": "own", "read": "subordinates", "update": None, "delete": None}
    """
    roles = await get_user_roles(db, user_id, component)

    # Start with no permissions
    effective = {
        "create": None,
        "read": None,
        "update": None,
        "delete": None,
    }

    for role in roles:
        for action, scope in role.permissions.items():
            if scope is None:
                continue

            current = effective.get(action)
            current_priority = SCOPE_PRIORITY.get(current, 0)
            new_priority = SCOPE_PRIORITY.get(scope, 0)

            # Keep the broadest scope (highest priority)
            if new_priority > current_priority:
                effective[action] = scope

    return effective


async def check_permission(
    db: AsyncSession,
    user_id: int,
    component: str,
    action: str,
    resource_owner_id: Optional[int] = None,
) -> bool:
    """Check if user has permission for an action on a component.

    Args:
        db: Database session
        user_id: User ID performing the action
        component: Component name (e.g., "tasks")
        action: Action to check ("create", "read", "update", "delete")
        resource_owner_id: Optional owner ID of the resource being accessed

    Returns:
        True if user has permission, False otherwise
    """
    permissions = await get_user_permissions(db, user_id, component)
    scope = permissions.get(action)

    if scope is None:
        return False

    if scope == "all":
        return True

    if scope == "own":
        # For create action, own is always allowed
        if action == "create":
            return True
        # For other actions, check ownership
        return resource_owner_id == user_id

    if scope == "subordinates":
        # For create action, subordinates scope allows creating own
        if action == "create":
            return True
        # Check if resource owner is in user's hierarchy
        if resource_owner_id is None:
            return False
        if resource_owner_id == user_id:
            return True
        return await is_in_hierarchy(db, user_id, resource_owner_id)

    return False


async def is_in_hierarchy(db: AsyncSession, manager_id: int, subordinate_id: int) -> bool:
    """Check if subordinate_id is anywhere in manager's tree.

    Walks up the chain from subordinate to see if they reach manager.

    Args:
        db: Database session
        manager_id: Potential manager user ID
        subordinate_id: Potential subordinate user ID

    Returns:
        True if subordinate is in manager's hierarchy
    """
    if manager_id == subordinate_id:
        return True

    visited: Set[int] = set()
    current_id = subordinate_id

    while current_id:
        if current_id in visited:
            # Cycle detected
            break
        visited.add(current_id)

        # Get current user's manager
        result = await db.execute(select(User.manager_id).where(User.id == current_id))
        current_manager = result.scalar_one_or_none()

        if current_manager == manager_id:
            return True

        current_id = current_manager

    return False


async def get_all_subordinate_ids(
    db: AsyncSession, manager_id: int, include_self: bool = True
) -> List[int]:
    """Get all subordinate IDs recursively in the hierarchy tree.

    Args:
        db: Database session
        manager_id: Manager user ID
        include_self: Whether to include manager_id in results

    Returns:
        List of user IDs in the hierarchy
    """
    ids: List[int] = [manager_id] if include_self else []
    to_process = [manager_id]
    visited: Set[int] = set()

    while to_process:
        current_id = to_process.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)

        # Get direct subordinates
        result = await db.execute(select(User.id).where(User.manager_id == current_id))
        direct = [row[0] for row in result.all()]

        ids.extend(direct)
        to_process.extend(direct)

    return ids


async def get_user_manager_chain(db: AsyncSession, user_id: int) -> List[User]:
    """Get the manager chain from user up to top.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of Users from user's manager up to top
    """
    chain = []
    visited: Set[int] = set()
    current_id = user_id

    while current_id:
        if current_id in visited:
            break
        visited.add(current_id)

        result = await db.execute(select(User).where(User.id == current_id))
        user = result.scalar_one_or_none()

        if not user or not user.manager_id:
            break

        # Get manager
        result = await db.execute(select(User).where(User.id == user.manager_id))
        manager = result.scalar_one_or_none()

        if manager:
            chain.append(manager)
            current_id = manager.id
        else:
            break

    return chain
