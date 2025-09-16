import httpx

from src.core.config import settings


class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.llm_model = settings.LLM_MODEL_NAME
        self.embedding_model = settings.EMBEDDING_MODEL_NAME

    async def _make_request(self, endpoint: str, payload: dict):
        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(f"{self.base_url}/api/{endpoint}", json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"Errore HTTP: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                print(f"Errore di connessione a Ollama: {e}")
                raise

    async def classify_question(self, question: str) -> str:
        prompt = f"""
        Sei un esperto di social media marketing. Il tuo compito è classificare la seguente domanda
        in una singola categoria concisa (massimo 2 parole).
        Esempi di categorie: 'Cucina Italiana', 'Sviluppo Web', 'Fitness', 'Marketing Digitale'.
        Domanda: "{question}"
        Categoria:
        """
        payload = {
            "model": self.llm_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        response = await self._make_request("generate", payload)
        return response.get("response", "Senza categoria").strip()

    async def create_embedding(self, text: str) -> list[float]:
        payload = {"model": self.embedding_model, "prompt": text}
        response = await self._make_request("embeddings", payload)
        return response.get("embedding", [])

    async def generate_content(self, question: str, context: str) -> str:
        prompt = f"""
        Sei un content creator per Instagram. Il tuo stile è informativo, coinvolgente e amichevole.
        Usando il contesto fornito, crea un post per Instagram che risponda alla domanda originale.
        Il post deve includere:
        1. Un titolo accattivante.
        2. Un corpo del testo chiaro e facile da leggere (usa emoji pertinenti).
        3. Una "call to action" finale (es. 'Salva il post!', 'Cosa ne pensi?').
        4. 3-5 hashtag pertinenti.

        CONTESTO:
        ---
        {context}
        ---

        DOMANDA ORIGINALE: "{question}"

        POST INSTAGRAM:
        """
        payload = {
            "model": self.llm_model,
            "prompt": prompt,
            "stream": False,
        }
        response = await self._make_request("generate", payload)
        return response.get("response", "Errore nella generazione del contenuto.").strip()
