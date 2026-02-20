"""Seed script for initial RBAC roles.

This script creates the default roles for each business component.
Run this after database migrations.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.models.role import Role


# Default roles for each component
DEFAULT_ROLES = {
    "tasks": [
        {
            "name": "User",
            "description": "Can create and manage own tasks only",
            "permissions": {
                "create": "own",
                "read": "own",
                "update": "own",
                "delete": "own",
            },
        },
        {
            "name": "Manager",
            "description": "Can manage own tasks and subordinates' tasks",
            "permissions": {
                "create": "own",
                "read": "subordinates",
                "update": "subordinates",
                "delete": None,  # Managers cannot delete others' tasks
            },
        },
        {
            "name": "Admin",
            "description": "Full access to all tasks",
            "permissions": {
                "create": "all",
                "read": "all",
                "update": "all",
                "delete": "all",
            },
        },
    ],
    # Add more components here as needed
    # "users": [...],
    # "audit": [...],
}


async def seed_roles(db: AsyncSession) -> None:
    """Create default roles if they don't exist."""
    print("Seeding RBAC roles...")

    for component, roles in DEFAULT_ROLES.items():
        for role_data in roles:
            # Check if role already exists
            from sqlalchemy import select

            result = await db.execute(
                select(Role).where(
                    Role.component == component,
                    Role.name == role_data["name"],
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  Role '{component}:{role_data['name']}' already exists, skipping")
                continue

            # Create role
            role = Role(
                component=component,
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
            )
            db.add(role)
            print(f"  Created role '{component}:{role_data['name']}'")

    await db.commit()
    print("✓ Role seeding complete")


async def main():
    """Main entry point for seeding."""
    async with async_session_maker() as db:
        await seed_roles(db)


if __name__ == "__main__":
    asyncio.run(main())
