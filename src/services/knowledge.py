# in src/services/knowledge.py

from serpapi import SerpApiClient

from src.core.config import settings


def google_search(query: str, num_results: int = 3) -> str:
    """
    Esegue una ricerca su Google usando SerpAPI e restituisce un contesto
    concatenando gli snippet dei risultati organici.
    """
    try:
        params = {
            "q": query,
            "api_key": settings.SERPAPI_API_KEY,
            "engine": "google",
            "gl": "it",  # Cerca in Italia
            "hl": "it",  # Lingua italiana
        }
        client = SerpApiClient(params)
        results = client.get_dict()

        organic_results = results.get("organic_results", [])

        # Prendi gli snippet dei primi 'num_results' risultati
        snippets = [item.get("snippet", "") for item in organic_results[:num_results] if "snippet" in item]

        if not snippets:
            return "Nessun risultato utile trovato nella ricerca."

        # Unisci gli snippet in un unico testo di contesto
        return " ".join(snippets).replace("\n", " ")

    except Exception as e:
        print(f"Errore durante la ricerca con SerpAPI: {e}")
        return "Nessuna informazione trovata a causa di un errore."
