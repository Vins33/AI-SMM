# /app/src/api/endpoints.py

import logging  # <-- 1. Importiamo il modulo di logging
import os
import shutil
from typing import Annotated, AsyncGenerator, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.database import (
    get_all_questions,
    get_db_session,
    reset_question_content,
)
from src.services.processing import classify_and_store_pipeline, generate_content_pipeline

# --- 2. CONFIGURAZIONE DEL LOGGING ---
# Aggiungiamo questa configurazione all'inizio del file.
# Stampa i log nel terminale (console) con un formato chiaro.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s", handlers=[logging.StreamHandler()]
)

router = APIRouter()


# --- MODELLI DI RISPOSTA (Pydantic) ---
class QuestionResponse(BaseModel):
    id: int
    question_text: str
    classification: str
    generated_content: str | None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str
    details: dict | None = None
    content: str | None = None


# --- DEPENDENCY ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_db_session() as db:
        yield db


# --- ENDPOINTS CON LOGGING INTEGRATO ---


@router.post("/process-csv/", response_model=MessageResponse, status_code=201)
async def process_csv(file: Annotated[UploadFile, File(...)], db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Il file deve essere in formato CSV.")

    file_path = f"./data/{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        result = await classify_and_store_pipeline(file_path, db)
        return {"message": "Elaborazione CSV completata con successo", "details": result}
    except Exception as e:
        # --- 3. LOGGING DELL'ERRORE ---
        # logging.exception cattura e stampa automaticamente l'intero traceback.
        logging.exception("ERRORE CRITICO durante l'elaborazione del CSV:")
        raise HTTPException(status_code=500, detail="Si è verificato un errore interno del server.") from e
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/generate-content/{question_id}", response_model=MessageResponse)
async def generate_content_endpoint(question_id: int, db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    try:
        content = await generate_content_pipeline(question_id, db)
        return {"message": "Contenuto generato con successo", "content": content}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        # --- 3. LOGGING DELL'ERRORE ---
        logging.exception(f"ERRORE CRITICO durante la generazione di contenuto per l'ID {question_id}:")
        raise HTTPException(status_code=500, detail="Si è verificato un errore interno del server.") from e


# (gli altri endpoint non hanno blocchi try/except complessi, quindi li lasciamo invariati per ora)


@router.get("/questions/", response_model=List[QuestionResponse])
async def get_questions_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    questions = await get_all_questions(db)
    return questions


@router.post("/questions/{question_id}/reset-content", response_model=MessageResponse)
async def reset_content_endpoint(question_id: int, db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    success = await reset_question_content(db, question_id)
    if success:
        return {"message": f"Contenuto per la domanda {question_id} resettato."}
    raise HTTPException(status_code=404, detail="Domanda non trovata.")
