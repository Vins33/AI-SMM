import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.database import get_question_by_id, save_question, update_question_content
from src.services.knowledge import google_search
from src.services.llm import OllamaService

# Creiamo un'istanza del servizio che useremo in tutto il file.
ollama_service = OllamaService()

# --- SINGOLE OPERAZIONI ---


async def classify_single_question(question_text: str, session: AsyncSession) -> str:
    """Classifica un singolo testo di domanda."""
    print(f"--- Classificazione per: '{question_text[:70]}...' ---")
    classification = await ollama_service.classify_question(question_text)
    print(f"--- Classificazione ottenuta: {classification} ---")
    return classification


async def generate_single_content(question_id: int, session: AsyncSession) -> str:
    """Genera il contenuto per una singola domanda, usando conoscenza esterna."""
    question_obj = await get_question_by_id(session, question_id)
    if not question_obj:
        raise FileNotFoundError(f"Domanda con ID {question_id} non trovata.")

    print(f"--- Ricerca conoscenza esterna per: '{question_obj.question_text[:70]}...' ---")

    # --- LA CORREZIONE È QUI ---
    # La funzione 'google_search' non è asincrona, quindi non si usa 'await'.
    knowledge = google_search(question_obj.question_text)

    print(f"--- Generazione contenuto con conoscenza: '{knowledge[:70]}...' ---")
    content = await ollama_service.generate_content(question_obj.question_text, knowledge)

    await update_question_content(session, question_id, content)
    print("--- Contenuto generato e salvato con successo. ---")
    return content


# --- PIPELINES COMPLETE ---


async def classify_and_store_pipeline(file_path: str, db: AsyncSession) -> dict:
    """Pipeline per leggere un CSV, classificare ogni domanda e salvarla."""
    df = pd.read_csv(file_path)
    processed_count = 0
    total_rows = len(df)

    for _, row in df.iterrows():
        question_text = f"{row.get('Title', '')}: {row.get('Body', '')}"
        classification = await classify_single_question(question_text, db)
        await save_question(db, question_text, classification)
        processed_count += 1
        print(f"--- Domanda {processed_count}/{total_rows} salvata nel DB. ---")

    return {"processed_count": processed_count, "total_rows": total_rows}


async def generate_content_pipeline(question_id: int, db: AsyncSession) -> str:
    """Pipeline per generare, salvare e restituire il contenuto."""
    content = await generate_single_content(question_id, db)
    return content
