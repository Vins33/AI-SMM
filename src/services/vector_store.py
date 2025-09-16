# in src/services/vector_store.py

from qdrant_client import QdrantClient, models

from src.core.config import settings


class VectorStoreService:
    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.collection_name = "instagram_content_kb"
        self._initialize_collection()

    def _initialize_collection(self):
        """
        Inizializza la collezione Qdrant, creandola SOLO se non esiste.
        Questo garantisce la persistenza dei dati tra i riavvii.
        """
        try:
            # Controlla se la collezione esiste già
            self.client.get_collection(collection_name=self.collection_name)
            print(f"-> Qdrant: Trovata collezione esistente '{self.collection_name}'")

        except Exception:
            # Se il client restituisce un errore (es. non trovata), la creiamo.
            print(f"-> Qdrant: Collezione non trovata. Creando '{self.collection_name}'...")

            # Assicurati che '768' sia la dimensione corretta per il tuo settings.EMBEDDING_MODEL_NAME
            # (Per nomic-embed-text, 768 è corretto).
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=768,
                    distance=models.Distance.COSINE
                ),
            )

    async def add_context(self, question_id: int, embedding: list[float], text: str):
        """Aggiunge un contesto vettorializzato alla collezione."""
        self.client.upsert(
            collection_name=self.collection_name,
            points=[models.PointStruct(id=question_id, vector=embedding, payload={"text": text})],
        )

    async def search(self, query_embedding: list[float], limit: int = 1) -> str:
        """Cerca i contesti più rilevanti nella collezione."""
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
        )
        if hits:
            return hits[0].payload.get("text", "")
        return "Nessun contesto rilevante trovato."
