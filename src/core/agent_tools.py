# Percorso file: src/core/agent_tools.py
# (Versione corretta che istanzia i client all'interno dei tool)

import asyncio
import json
import uuid

from langchain.tools import tool
from pydantic import BaseModel, Field

from src.services.financial import StockAnalysisSchema, _analyze_stock_sync
from src.services.knowledge import google_search
from src.services.llm import OllamaService
from src.services.vector_store import VectorStoreService


class WebSearchSchema(BaseModel):
    """Schema per il tool di ricerca web."""
    query: str = Field(description="La stringa di ricerca ottimizzata da inviare a Google.")

class KBReadSchema(BaseModel):
    """Schema per il tool di lettura dalla Knowledge Base."""
    query: str = Field(description="La domanda o l'argomento da cercare nel database vettoriale interno (KB).")

class KBWriteSchema(BaseModel):
    """Schema per il tool di scrittura nella Knowledge Base."""
    content: str = Field(description="L'informazione testuale o il fatto da salvare e vettorializzare nella KB.")

@tool("web_search_tool", args_schema=WebSearchSchema)
async def web_search_tool(query: str) -> str:
    """
    Usa questo tool per cercare informazioni aggiornate o eventi recenti sul web tramite Google.
    Non usarlo per informazioni già presenti nella Knowledge Base.
    Utilizzalo massimo 2 volte.
    """
    print(f"--- TOOL: Eseguo web_search_tool (Query: {query}) ---")
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, google_search, query, 1)
        print(result)
        return result
    except Exception as e:
        return f"Errore durante l'esecuzione della ricerca: {str(e)}"


@tool("read_from_kb_tool", args_schema=KBReadSchema)
async def read_from_kb_tool(query: str) -> str:
    """
    Usa questo tool per recuperare informazioni precedentemente salvate
    dalla Knowledge Base (KB) vettoriale interna.
    """
    print(f"--- TOOL: Eseguo read_from_kb_tool (Query: {query}) ---")

    ollama_cli = OllamaService()
    vector_store_cli = VectorStoreService()

    try:
        # 1. Crea l'embedding
        embedding = await ollama_cli.create_embedding(query)
        if not embedding:
            return "Errore: impossibile creare l'embedding per la query."

        context = await vector_store_cli.search(embedding, limit=1)
        return context
    except Exception as e:
        return f"Errore durante la lettura dal Vector DB: {str(e)}"


@tool("write_to_kb_tool", args_schema=KBWriteSchema)
async def write_to_kb_tool(content: str) -> str:
    """
    Usa questo tool per salvare permanentemente (scrivere) un nuovo fatto o un'informazione
    nella Knowledge Base (KB) vettoriale interna per recuperi futuri.
    """
    print(f"--- TOOL: Eseguo write_to_kb_tool (Content: {content[:30]}...) ---")

    ollama_cli = OllamaService()
    vector_store_cli = VectorStoreService()

    try:
        embedding = await ollama_cli.create_embedding(content)
        if not embedding:
            return "Errore: impossibile creare l'embedding per il contenuto."

        point_id = uuid.uuid4().int & (1<<63)-1

        await vector_store_cli.add_context(
            question_id=point_id,
            embedding=embedding,
            text=content
        )
        return f"Informazione salvata con successo nella KB (ID: {point_id})."
    except Exception as e:
        return f"Errore durante la scrittura sul Vector DB: {str(e)}"

@tool("stock_scoring_tool", args_schema=StockAnalysisSchema)
async def stock_scoring_tool(ticker: str) -> str:
    """
    Usa questo tool per calcolare uno score (BUY/HOLD/SELL) del titolo
    tramite indicatori base (P/E, ROE, D/E, Beta, Dividend Yield, Growth, EV/EBITDA)
    estratti con yfinance.
    Restituisce un JSON testuale con metriche, score e decisione.
    """
    print(f"--- TOOL: Eseguo stock_scoring_tool (Ticker: {ticker}) ---")
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _analyze_stock_sync, ticker)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps(
            {"ticker": ticker, "error": f"Errore durante l'analisi del titolo: {str(e)}"},
            ensure_ascii=False,
        )

available_tools_list = [web_search_tool, read_from_kb_tool, write_to_kb_tool, stock_scoring_tool]
