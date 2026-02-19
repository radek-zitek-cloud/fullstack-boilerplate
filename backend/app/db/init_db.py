import asyncio

from alembic import command
from alembic.config import Config
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, engine
from app.core.security import get_password_hash
from app.models.base import Base
from app.models.user import User

settings = get_settings()


async def init_db():
    """Initialize database and create first admin user."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if admin exists
        result = await db.execute(select(User).where(User.email == settings.FIRST_ADMIN_EMAIL))
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                email=settings.FIRST_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
                is_admin=True,
            )
            db.add(admin)
            await db.commit()
            print(f"Created admin user: {settings.FIRST_ADMIN_EMAIL}")
        else:
            print(f"Admin user already exists: {settings.FIRST_ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(init_db())
