# src/api/middleware/explainability.py
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from src.api.services.ollama_client import run_ollama

# Percorso audit logs integrato con AI-SMM
AUDIT_LOG_PATH = Path("src/data/audit_logs.json")
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_logs() -> list[dict[str, Any]]:
    if AUDIT_LOG_PATH.exists():
        try:
            return json.loads(AUDIT_LOG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []

def save_log(entry: dict[str, Any]) -> None:
    logs = load_logs()
    logs.append(entry)
    AUDIT_LOG_PATH.write_text(json.dumps(logs, indent=2, ensure_ascii=False), encoding="utf-8")


async def explainability_middleware(request: Request, call_next):
    """
    Middleware Explainability per AI-SMM:
    - misura latenza di generazione
    - aggiunge spiegazione del modello
    - salva log JSON per la dashboard Streamlit
    """
    if not request.url.path.endswith("/ollama/generate"):
        return await call_next(request)

    try:
        body = await request.json()
    except Exception:
        body = {}

    session_id = str(uuid.uuid4())
    prompt = body.get("prompt", "")
    model = body.get("model", "llama3.2")
    t0 = time.perf_counter()


    response_data = await run_ollama(model, prompt)

    t1 = time.perf_counter()
    latency = round(t1 - t0, 3)

    # Genera spiegazione con mini prompt
    explanation_prompt = f"Spiega brevemente come hai costruito la seguente risposta:\n\n{response_data['response']}"
    explanation_data = await run_ollama(model, explanation_prompt)

    record = {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "model": model,
        "prompt": prompt,
        "response": response_data.get("response"),
        "explanation": explanation_data.get("response"),
        "tokens": response_data.get("tokens", 0),
        "latency": latency,
        "confidence": response_data.get("confidence", 0.9),
        "hallucination": 0.0,
    }

    save_log(record)
    return JSONResponse({"status": "ok", "audit_id": session_id, **record})
