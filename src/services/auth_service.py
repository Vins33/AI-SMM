# src/services/auth_service.py
"""Authentication service for user management."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import get_password_hash, verify_password
from src.services.auth_models import User, UserRole


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    """Get a user by username."""
    result = await session.execute(select(User).filter(User.username == username))
    return result.scalars().first()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Get a user by email."""
    result = await session.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Get a user by ID."""
    result = await session.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()


async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    password: str,
    role: UserRole = UserRole.USER,
) -> User:
    """Create a new user."""
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role.value,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    """Authenticate a user by username and password."""
    user = await get_user_by_username(session, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await session.commit()
    return user


async def get_all_users(session: AsyncSession) -> list[User]:
    """Get all users (for admin)."""
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def update_user(
    session: AsyncSession,
    user_id: int,
    username: str | None = None,
    email: str | None = None,
    password: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> User | None:
    """Update a user's information."""
    user = await get_user_by_id(session, user_id)
    if not user:
        return None

    if username is not None:
        user.username = username
    if email is not None:
        user.email = email
    if password is not None:
        user.hashed_password = get_password_hash(password)
    if role is not None:
        user.role = role.value
    if is_active is not None:
        user.is_active = is_active

    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: int) -> bool:
    """Delete a user by ID."""
    user = await get_user_by_id(session, user_id)
    if user:
        await session.delete(user)
        await session.commit()
        return True
    return False


async def ensure_sysadmin_exists(session: AsyncSession) -> None:
    """Ensure at least one sysadmin user exists."""
    result = await session.execute(
        select(User).filter(User.role == UserRole.SYSADMIN.value)
    )
    sysadmin = result.scalars().first()

    if not sysadmin:
        # Create default sysadmin
        await create_user(
            session,
            username=settings.SYSADMIN_USERNAME,
            email=settings.SYSADMIN_EMAIL,
            password=settings.SYSADMIN_PASSWORD,
            role=UserRole.SYSADMIN,
        )
