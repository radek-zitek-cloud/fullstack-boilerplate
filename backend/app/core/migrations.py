"""Database migration utilities for automatic schema upgrades on startup.

This module provides functionality to check and run Alembic migrations
automatically when the application starts, ensuring the database schema
is always up to date.
"""

import asyncio
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_alembic_config() -> Config:
    """Get Alembic configuration from alembic.ini or defaults."""
    backend_dir = Path(__file__).parent.parent.parent
    alembic_ini = backend_dir / "alembic.ini"

    if alembic_ini.exists():
        config = Config(str(alembic_ini))
    else:
        config = Config()
        config.set_main_option("script_location", str(backend_dir / "alembic"))
        settings = get_settings()
        config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    return config


def is_migration_needed_sync() -> bool:
    """Check if database migrations are needed (sync version)."""
    try:
        config = get_alembic_config()
        script = ScriptDirectory.from_config(config)

        settings = get_settings()
        sync_url = settings.DATABASE_URL.replace("+aiosqlite", "")
        engine = create_engine(sync_url, echo=False)

        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='alembic_version'"
                )
            )
            if result.scalar() is None:
                return True

            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_rev = result.scalar()
            head_rev = script.get_current_head()

            if current_rev != head_rev:
                logger.info(f"Migration needed: current={current_rev}, head={head_rev}")
                return True

            return False

    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return True


def run_migrations_sync() -> None:
    """Run all pending database migrations."""
    try:
        config = get_alembic_config()
        logger.info("Running database migrations...")
        command.upgrade(config, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise


async def check_and_migrate() -> None:
    """Check if migrations are needed and run them."""
    settings = get_settings()

    if not settings.AUTO_MIGRATE:
        logger.info("AUTO_MIGRATE is disabled - skipping migration check")
        return

    if os.environ.get("UVICORN_RELOAD") == "true":
        logger.info("Uvicorn reload mode detected - skipping migrations")
        return

    if "pytest" in os.environ.get("PYTEST_CURRENT_TEST", ""):
        logger.debug("Test environment detected - skipping migrations")
        return

    try:
        needs_migration = await asyncio.to_thread(is_migration_needed_sync)

        if needs_migration:
            await asyncio.to_thread(run_migrations_sync)
        else:
            logger.debug("Database is up to date - no migrations needed")

    except Exception as e:
        logger.error(f"Migration check failed: {e}")
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(f"Failed to run database migrations: {e}") from e
        else:
            logger.warning("Continuing despite migration failure (development mode)")
