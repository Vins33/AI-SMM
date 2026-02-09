# src/services/auth_service.py
"""Authentication service for user management."""

import json
from datetime import datetime, timezone

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import get_password_hash, verify_password
from src.services.auth_models import AuditLog, TokenBlacklist, User, UserRole

# --- User CRUD ---


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


async def authenticate_user(session: AsyncSession, username: str, password: str) -> User | None:
    """Authenticate a user by username and password with lockout support."""
    user = await get_user_by_username(session, username)
    if not user:
        return None

    # Check if account is locked
    if user.locked_until:
        now = datetime.now(timezone.utc)
        locked = user.locked_until
        if locked.tzinfo is None:
            locked = locked.replace(tzinfo=timezone.utc)
        if now < locked:
            return None  # Still locked
        else:
            # Lockout expired, reset
            user.failed_login_attempts = 0
            user.locked_until = None

    if not verify_password(password, user.hashed_password):
        # Increment failed attempts
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            from datetime import timedelta

            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
        await session.commit()
        return None

    # Successful login: reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    await session.commit()
    return user


async def get_all_users(
    session: AsyncSession,
    search: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> tuple[list[User], int]:
    """Get all users with optional search and pagination. Returns (users, total_count)."""
    base_query = select(User)

    if search:
        search_filter = f"%{search}%"
        base_query = base_query.filter(
            or_(
                User.username.ilike(search_filter),
                User.email.ilike(search_filter),
                User.role.ilike(search_filter),
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    # Get paginated results
    users_query = base_query.order_by(User.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(users_query)
    users = list(result.scalars().all())

    return users, total


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
    result = await session.execute(select(User).filter(User.role == UserRole.SYSADMIN.value))
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


# --- Token Blacklist ---


async def blacklist_token(session: AsyncSession, token_jti: str, user_id: int, expires_at: datetime) -> None:
    """Add a token to the blacklist."""
    entry = TokenBlacklist(
        token_jti=token_jti,
        user_id=user_id,
        expires_at=expires_at,
    )
    session.add(entry)
    await session.commit()


async def is_token_blacklisted(session: AsyncSession, token_jti: str) -> bool:
    """Check if a token JTI is blacklisted."""
    result = await session.execute(select(TokenBlacklist).filter(TokenBlacklist.token_jti == token_jti))
    return result.scalars().first() is not None


async def cleanup_expired_blacklist(session: AsyncSession) -> int:
    """Remove expired tokens from blacklist. Returns count of removed entries."""
    now = datetime.now(timezone.utc)
    result = await session.execute(delete(TokenBlacklist).where(TokenBlacklist.expires_at < now))
    await session.commit()
    return result.rowcount


# --- Audit Log ---


async def create_audit_log(
    session: AsyncSession,
    action: str,
    user_id: int | None = None,
    username: str | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    details: dict | str | None = None,
    ip_address: str | None = None,
) -> None:
    """Create an audit log entry."""
    if isinstance(details, dict):
        details = json.dumps(details)
    entry = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    session.add(entry)
    await session.commit()


async def get_audit_logs(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 50,
    action: str | None = None,
    user_id: int | None = None,
) -> tuple[list[AuditLog], int]:
    """Get audit logs with optional filters and pagination."""
    base_query = select(AuditLog)

    if action:
        base_query = base_query.filter(AuditLog.action == action)
    if user_id is not None:
        base_query = base_query.filter(AuditLog.user_id == user_id)

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await session.execute(count_query)).scalar() or 0

    logs_query = base_query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(logs_query)
    logs = list(result.scalars().all())

    return logs, total
