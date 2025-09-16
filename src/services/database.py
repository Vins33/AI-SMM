# /app/src/services/database.py - VERSIONE COMPLETAMENTE ASINCRONA

import contextlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.services.models import ClassifiedQuestion

# --- Unica Configurazione Asincrona ---
# Rimuoviamo create_engine, SessionLocal e tutto il blocco sincrono.
async_engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession)


# Unico gestore di sessione, asincrono
@contextlib.asynccontextmanager
async def get_db_session():
    async_db = AsyncSessionLocal()
    try:
        yield async_db
    finally:
        await async_db.close()


# --- Funzioni di Interazione DB (TUTTE ASINCRONE) ---
# Nota: usiamo la sintassi moderna di SQLAlchemy 2.0 con select()


async def save_question(session: AsyncSession, question_text: str, classification: str) -> ClassifiedQuestion:
    """Salva una domanda classificata nel DB in modo asincrono."""
    db_question = ClassifiedQuestion(question_text=question_text, classification=classification)
    session.add(db_question)
    await session.commit()
    await session.refresh(db_question)
    return db_question


async def update_question_content(session: AsyncSession, question_id: int, content: str):
    """Aggiorna il contenuto generato per una domanda esistente in modo asincrono."""
    result = await session.execute(select(ClassifiedQuestion).filter(ClassifiedQuestion.id == question_id))
    db_question = result.scalars().first()

    if db_question:
        db_question.generated_content = content
        await session.commit()


async def get_question_by_id(session: AsyncSession, question_id: int) -> ClassifiedQuestion | None:
    """Recupera una domanda per ID in modo asincrono."""
    result = await session.execute(select(ClassifiedQuestion).filter(ClassifiedQuestion.id == question_id))
    return result.scalars().first()


async def get_all_questions(session: AsyncSession) -> list[ClassifiedQuestion]:
    """Recupera tutte le domande in modo asincrono."""
    result = await session.execute(select(ClassifiedQuestion).order_by(ClassifiedQuestion.id.desc()))
    return result.scalars().all()


async def reset_question_content(session: AsyncSession, question_id: int) -> bool:
    """Resetta il contenuto di una domanda in modo asincrono."""
    result = await session.execute(select(ClassifiedQuestion).filter(ClassifiedQuestion.id == question_id))
    db_question = result.scalars().first()

    if db_question:
        db_question.generated_content = None
        await session.commit()
        return True
    return False
