# src/api/auth.py
"""Authentication API endpoints."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    validate_password_strength,
    verify_password,
)
from src.services.auth_models import User, UserRole
from src.services.auth_service import (
    authenticate_user,
    blacklist_token,
    create_audit_log,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    is_token_blacklisted,
    update_user,
)
from src.services.database import AsyncSessionLocal
from src.services.models import Conversation, Message

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# --- Pydantic Schemas ---


class UserCreate(BaseModel):
    """Schema for user registration."""

    username: str
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for user profile update."""

    username: str | None = None
    email: EmailStr | None = None
    current_password: str | None = None
    new_password: str | None = None


class UserResponse(BaseModel):
    """Schema for user response."""

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime | None = None
    last_login: datetime | None = None

    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    """Schema for user statistics."""

    total_conversations: int
    total_messages: int
    messages_sent: int
    messages_received: int
    first_activity: datetime | None = None
    last_activity: datetime | None = None
    avg_messages_per_conversation: float
    account_age_days: int


class Token(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class DeleteAccountRequest(BaseModel):
    """Schema for account self-deletion."""

    password: str
    confirmation: str = "DELETE"


# --- Dependencies ---


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Check token type (must be access token)
    if payload.get("type") != "access":
        raise credentials_exception

    # Check if token is blacklisted
    jti = payload.get("jti")
    if jti and await is_token_blacklisted(session, jti):
        raise credentials_exception

    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await get_user_by_id(session, int(user_id))
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get the current user and verify they are an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


async def get_current_sysadmin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get the current user and verify they are a sysadmin."""
    if not current_user.is_sysadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sysadmin privileges required",
        )
    return current_user


# --- Helpers ---


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _create_tokens(user: User) -> tuple[str, str, str]:
    """Create access and refresh tokens with JTI. Returns (access_token, refresh_token, access_jti)."""
    jti = str(uuid.uuid4())
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role, "jti": jti},
        expires_delta=access_token_expires,
    )
    refresh_jti = str(uuid.uuid4())
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "username": user.username, "jti": refresh_jti}
    )
    return access_token, refresh_token, jti


# --- Endpoints ---


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user."""
    # Validate password strength
    password_errors = validate_password_strength(user_data.password)
    if password_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(password_errors),
        )

    # Check if username exists
    existing_user = await get_user_by_username(session, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    existing_email = await get_user_by_email(session, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await create_user(
        session,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        role=UserRole.USER,
    )

    # Audit log
    await create_audit_log(
        session,
        action="user_registered",
        user_id=user.id,
        username=user.username,
        target_type="user",
        target_id=user.id,
        ip_address=_get_client_ip(request),
    )

    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Login and get access token."""
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        # Check if account is locked
        locked_user = await get_user_by_username(session, form_data.username)
        if locked_user and locked_user.locked_until:
            now = datetime.now(timezone.utc)
            locked_until = locked_user.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if now < locked_until:
                remaining = int((locked_until - now).total_seconds() // 60) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Account bloccato per troppi tentativi. Riprova tra {remaining} minuti.",
                )

        # Audit failed login
        await create_audit_log(
            session,
            action="login_failed",
            username=form_data.username,
            details={"reason": "invalid_credentials"},
            ip_address=_get_client_ip(request),
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username o password non corretti",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disattivato",
        )

    access_token, refresh_token, _ = _create_tokens(user)

    # Audit successful login
    await create_audit_log(
        session,
        action="login_success",
        user_id=user.id,
        username=user.username,
        ip_address=_get_client_ip(request),
    )

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout")
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Logout and blacklist current token."""
    payload = decode_access_token(token)
    if payload:
        jti = payload.get("jti")
        user_id = payload.get("sub")
        exp = payload.get("exp")
        if jti and user_id and exp:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
            await blacklist_token(session, jti, int(user_id), expires_at)

            await create_audit_log(
                session,
                action="logout",
                user_id=int(user_id),
                username=payload.get("username"),
                ip_address=_get_client_ip(request),
            )

    return {"detail": "Logout effettuato con successo"}


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    token_data: TokenRefresh,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Refresh access token using refresh token."""
    payload = decode_access_token(token_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if refresh token is blacklisted
    old_jti = payload.get("jti")
    if old_jti and await is_token_blacklisted(session, old_jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocato",
        )

    user_id = payload.get("sub")
    user = await get_user_by_id(session, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Blacklist old refresh token
    if old_jti:
        exp = payload.get("exp")
        if exp:
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
            await blacklist_token(session, old_jti, int(user_id), expires_at)

    access_token, new_refresh_token, _ = _create_tokens(user)

    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Update current user's profile information."""
    # If changing password, verify current password
    if user_data.new_password:
        if not user_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La password attuale è richiesta per cambiare password",
            )
        if not verify_password(user_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password attuale non corretta",
            )

        # Validate new password strength
        password_errors = validate_password_strength(user_data.new_password)
        if password_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="; ".join(password_errors),
            )

    # Check username uniqueness
    if user_data.username and user_data.username != current_user.username:
        existing = await get_user_by_username(session, user_data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username già in uso",
            )

    # Check email uniqueness
    if user_data.email and user_data.email != current_user.email:
        existing = await get_user_by_email(session, user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email già in uso",
            )

    updated = await update_user(
        session,
        current_user.id,
        username=user_data.username,
        email=user_data.email,
        password=user_data.new_password,
    )

    # Audit log
    changes = {}
    if user_data.username and user_data.username != current_user.username:
        changes["username"] = {"old": current_user.username, "new": user_data.username}
    if user_data.email and str(user_data.email) != current_user.email:
        changes["email"] = {"old": current_user.email, "new": str(user_data.email)}
    if user_data.new_password:
        changes["password"] = "changed"

    if changes:
        await create_audit_log(
            session,
            action="profile_updated",
            user_id=current_user.id,
            username=current_user.username,
            target_type="user",
            target_id=current_user.id,
            details=changes,
            ip_address=_get_client_ip(request),
        )

    return updated


@router.delete("/me")
async def delete_me(
    delete_data: DeleteAccountRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete current user's account (self-service)."""
    # Sysadmin cannot self-delete via this endpoint
    if current_user.is_sysadmin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gli account sysadmin non possono essere eliminati da qui",
        )

    # Verify confirmation text
    if delete_data.confirmation != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conferma l'eliminazione digitando 'DELETE'",
        )

    # Verify password
    if not verify_password(delete_data.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password non corretta",
        )

    # Audit log before deletion
    await create_audit_log(
        session,
        action="account_self_deleted",
        user_id=current_user.id,
        username=current_user.username,
        target_type="user",
        target_id=current_user.id,
        ip_address=_get_client_ip(request),
    )

    # Delete user
    from src.services.auth_service import delete_user

    await delete_user(session, current_user.id)

    return {"detail": "Account eliminato con successo"}


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    """Get current user's usage statistics."""
    # Total conversations for this user
    conv_result = await session.execute(
        select(func.count(Conversation.id)).filter(Conversation.user_id == current_user.id)
    )
    total_conversations = conv_result.scalar() or 0

    # Total messages in this user's conversations
    msg_result = await session.execute(
        select(func.count(Message.id)).join(Conversation).filter(Conversation.user_id == current_user.id)
    )
    total_messages = msg_result.scalar() or 0

    # Messages sent by user (role="user") in their conversations
    sent_result = await session.execute(
        select(func.count(Message.id))
        .join(Conversation)
        .filter(Conversation.user_id == current_user.id, Message.role == "user")
    )
    messages_sent = sent_result.scalar() or 0

    # Messages received (agent responses) in their conversations
    received_result = await session.execute(
        select(func.count(Message.id))
        .join(Conversation)
        .filter(Conversation.user_id == current_user.id, Message.role == "assistant")
    )
    messages_received = received_result.scalar() or 0

    # First activity (oldest message in user's conversations)
    first_result = await session.execute(
        select(func.min(Message.timestamp)).join(Conversation).filter(Conversation.user_id == current_user.id)
    )
    first_activity = first_result.scalar()

    # Last activity (newest message in user's conversations)
    last_result = await session.execute(
        select(func.max(Message.timestamp)).join(Conversation).filter(Conversation.user_id == current_user.id)
    )
    last_activity = last_result.scalar()

    # Average messages per conversation
    avg_messages = total_messages / total_conversations if total_conversations > 0 else 0.0

    # Account age
    now = datetime.now(timezone.utc)
    created = current_user.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    account_age_days = (now - created).days if created else 0

    return UserStatsResponse(
        total_conversations=total_conversations,
        total_messages=total_messages,
        messages_sent=messages_sent,
        messages_received=messages_received,
        first_activity=first_activity,
        last_activity=last_activity,
        avg_messages_per_conversation=round(avg_messages, 1),
        account_age_days=account_age_days,
    )
