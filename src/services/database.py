# src/services/database.py
"""Async database service using SQLAlchemy 2.0."""

import contextlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.services.models import Base, Conversation, Message

# Async Engine and Session
async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextlib.asynccontextmanager
async def get_db_session():
    """Async context manager for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    # Import auth models to ensure they are registered with Base
    from src.services.auth_models import User  # noqa: F401

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Ensure sysadmin exists
    from src.services.auth_service import ensure_sysadmin_exists

    async with AsyncSessionLocal() as session:
        await ensure_sysadmin_exists(session)


# --- Conversation CRUD ---


async def create_conversation(
    session: AsyncSession, title: str = "Nuova conversazione"
) -> Conversation:
    """Create a new conversation."""
    conv = Conversation(title=title)
    session.add(conv)
    await session.commit()
    await session.refresh(conv)
    return conv


async def get_conversations(session: AsyncSession) -> list[Conversation]:
    """Get all conversations ordered by update time."""
    result = await session.execute(
        select(Conversation).order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation(
    session: AsyncSession, conv_id: int
) -> Conversation | None:
    """Get a single conversation by ID."""
    result = await session.execute(
        select(Conversation).filter(Conversation.id == conv_id)
    )
    return result.scalars().first()


async def delete_conversation(session: AsyncSession, conv_id: int) -> bool:
    """Delete a conversation by ID."""
    conv = await get_conversation(session, conv_id)
    if conv:
        await session.delete(conv)
        await session.commit()
        return True
    return False


# --- Message CRUD ---


async def add_message(
    session: AsyncSession, conv_id: int, role: str, content: str
) -> Message:
    """Add a message to a conversation."""
    msg = Message(conversation_id=conv_id, role=role, content=content)
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def get_messages(session: AsyncSession, conv_id: int) -> list[Message]:
    """Get all messages for a conversation."""
    result = await session.execute(
        select(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.timestamp)
    )
    return list(result.scalars().all())


async def update_conversation_title(
    session: AsyncSession, conv_id: int, title: str
) -> bool:
    """Update the title of a conversation."""
    conv = await get_conversation(session, conv_id)
    if conv:
        conv.title = title
        await session.commit()
        return True
    return False
