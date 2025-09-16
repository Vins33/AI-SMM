# Percorso file: src/core/agent_tools.py
# (Versione corretta che istanzia i client all'interno dei tool)

import asyncio
import uuid

from langchain.tools import tool
from pydantic import BaseModel, Field

from src.services.knowledge import google_search

# Importiamo i TUOI servizi esistenti dal tuo codice
from src.services.llm import OllamaService
from src.services.vector_store import VectorStoreService


# --- 1. Schemi Pydantic (args_schema) ---
# (Invariati)
class WebSearchSchema(BaseModel):
    """Schema per il tool di ricerca web."""
    query: str = Field(description="La stringa di ricerca ottimizzata da inviare a Google.")

class KBReadSchema(BaseModel):
    """Schema per il tool di lettura dalla Knowledge Base."""
    query: str = Field(description="La domanda o l'argomento da cercare nel database vettoriale interno (KB).")

class KBWriteSchema(BaseModel):
    """Schema per il tool di scrittura nella Knowledge Base."""
    content: str = Field(description="L'informazione testuale o il fatto da salvare e vettorializzare nella KB.")


# --- 2. NESSUNA ISTANZA GLOBALE DEI SERVIZI ---
# ollama_service = OllamaService()        <-- RIMOSSO
# vector_store_service = VectorStoreService() <-- RIMOSSO


# --- 3. Definizione dei Tool ---

@tool(args_schema=WebSearchSchema)
async def web_search_tool(query: str) -> str:
    """
    Usa questo tool per cercare informazioni aggiornate o eventi recenti sul web tramite Google.
    Non usarlo per informazioni già presenti nella Knowledge Base.
    """
    print(f"--- TOOL: Eseguo web_search_tool (Query: {query}) ---")
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, google_search, query, 3)
        return result
    except Exception as e:
        return f"Errore durante l'esecuzione della ricerca: {str(e)}"


@tool(args_schema=KBReadSchema)
async def read_from_kb_tool(query: str) -> str:
    """
    Usa questo tool per recuperare informazioni precedentemente salvate
    dalla Knowledge Base (KB) vettoriale interna.
    """
    print(f"--- TOOL: Eseguo read_from_kb_tool (Query: {query}) ---")

    # --- ISTANZIAMO I SERVIZI QUI ---
    # Questo assicura che vivano sull'event loop corretto.
    ollama_cli = OllamaService()
    vector_store_cli = VectorStoreService()

    try:
        # 1. Crea l'embedding
        embedding = await ollama_cli.create_embedding(query)
        if not embedding:
            return "Errore: impossibile creare l'embedding per la query."

        # 2. Cerca nel VectorStore (usando il client istanziato ora
        # Nota: il tuo metodo .search è sync, ma lo chiamiamo con await
        # perché lo hai definito 'async def' nel tuo file originale.
        context = await vector_store_cli.search(embedding, limit=1)
        return context
    except Exception as e:
        return f"Errore durante la lettura dal Vector DB: {str(e)}"


@tool(args_schema=KBWriteSchema)
async def write_to_kb_tool(content: str) -> str:
    """
    Usa questo tool per salvare permanentemente (scrivere) un nuovo fatto o un'informazione
    nella Knowledge Base (KB) vettoriale interna per recuperi futuri.
    """
    print(f"--- TOOL: Eseguo write_to_kb_tool (Content: {content[:30]}...) ---")

    # --- ISTANZIAMO I SERVIZI ANCHE QUI ---
    ollama_cli = OllamaService()
    vector_store_cli = VectorStoreService()

    try:
        # 1. Crea l'embedding
        embedding = await ollama_cli.create_embedding(content)
        if not embedding:
            return "Errore: impossibile creare l'embedding per il contenuto."

        # 2. Genera ID
        point_id = uuid.uuid4().int & (1<<63)-1

        # 3. Salva nel VectorStore (usando il client istanziato ora)
        await vector_store_cli.add_context(
            question_id=point_id,
            embedding=embedding,
            text=content
        )
        return f"Informazione salvata con successo nella KB (ID: {point_id})."
    except Exception as e:
        return f"Errore durante la scrittura sul Vector DB: {str(e)}"


# Esportiamo la lista di tutti i tool (questo non cambia)
available_tools_list = [web_search_tool, read_from_kb_tool, write_to_kb_tool]
