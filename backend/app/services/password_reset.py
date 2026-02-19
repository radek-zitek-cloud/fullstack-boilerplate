"""Password reset service for managing reset tokens."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.password_reset_token import PasswordResetToken
from app.models.user import User


async def create_reset_token(user_id: int, db: AsyncSession) -> str:
    """Create a new password reset token.
    
    Args:
        user_id: The ID of the user requesting password reset
        db: Database session
        
    Returns:
        The generated token string
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    reset_token = PasswordResetToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(reset_token)
    await db.commit()
    
    return token


async def validate_reset_token(token: str, db: AsyncSession) -> Optional[User]:
    """Validate a reset token and return the user if valid.
    
    Args:
        token: The reset token to validate
        db: Database session
        
    Returns:
        The User if token is valid, None otherwise
    """
    result = await db.execute(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token == token,
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
            PasswordResetToken.used == False
        )
        .options(selectinload(PasswordResetToken.user))
    )
    reset_token = result.scalar_one_or_none()
    
    if reset_token and reset_token.user:
        return reset_token.user
    return None


async def mark_token_used(token: str, db: AsyncSession) -> None:
    """Mark a reset token as used.
    
    Args:
        token: The token to mark as used
        db: Database session
    """
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == token)
    )
    reset_token = result.scalar_one_or_none()
    if reset_token:
        reset_token.used = True
        await db.commit()
