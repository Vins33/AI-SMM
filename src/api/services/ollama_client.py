import json

import aiohttp

OLLAMA_URL = "http://ollama:11434/api/generate"
async def run_ollama(model: str, prompt: str) -> dict:
    """
    Effettua una richiesta asincrona a Ollama.
    """
    payload = {"model": model, "prompt": prompt}
    async with aiohttp.ClientSession() as session:
        async with session.post(OLLAMA_URL, json=payload) as resp:
            if resp.status != 200:
                return {"response": f"Errore Ollama: {resp.status}", "tokens": 0, "confidence": 0.0}

            raw_text = await resp.text()
            try:
                lines = [json.loads(line) for line in raw_text.strip().split("\n") if line.strip()]
                text = "".join([line.get("response", "") for line in lines])
                tokens = sum([line.get("eval_count", 0) for line in lines])
                return {"response": text.strip(), "tokens": tokens, "confidence": 0.9}
            except Exception:
                return {"response": raw_text, "tokens": 0, "confidence": 0.5}
    return {"response": "Errore sconosciuto durante la comunicazione con Ollama.", "tokens": 0, "confidence": 0.0}
