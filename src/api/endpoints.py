# src/api/endpoints.py
"""FastAPI API endpoints (legacy - protected with authentication)."""

import logging
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.services.auth_models import User
from src.services.database import (
    AsyncSessionLocal,
    add_message,
    create_conversation,
    get_conversations,
    get_messages,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    handlers=[logging.StreamHandler()],
)

router = APIRouter()


# --- Pydantic Schemas ---


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""

    title: str = "Nuova conversazione"


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: int
    title: str

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    role: str
    content: str


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: int
    conversation_id: int
    role: str
    content: str

    class Config:
        from_attributes = True


# --- Dependency ---


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


db_dependency = Depends(get_db)


# --- Endpoints (now protected) ---


@router.get("/conversations/", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = db_dependency,
):
    """Get all conversations for the current user."""
    return await get_conversations(session, user_id=current_user.id)


@router.post("/conversations/", response_model=ConversationResponse)
async def new_conversation(
    data: ConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = db_dependency,
):
    """Create a new conversation for the current user."""
    return await create_conversation(session, data.title, user_id=current_user.id)


@router.get(
    "/conversations/{conv_id}/messages/", response_model=list[MessageResponse]
)
async def list_messages(
    conv_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = db_dependency,
):
    """Get all messages for a conversation."""
    return await get_messages(session, conv_id)


@router.post(
    "/conversations/{conv_id}/messages/", response_model=MessageResponse
)
async def new_message(
    conv_id: int,
    data: MessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = db_dependency,
):
    """Add a message to a conversation."""
    return await add_message(session, conv_id, data.role, data.content)
