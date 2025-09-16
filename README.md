.
├── .env                  # File per le variabili d'ambiente (es. SERPAPI_API_KEY)
├── .gitignore            # File standard di Git per ignorare file e cartelle
├── data/
│   └── Questions.csv     # Dati di input di esempio
├── docker-compose.yml    # Gestisce tutti i servizi (Streamlit UI, Ollama, Postgres, Qdrant)
├── Dockerfile            # Costruisce l'immagine Python principale (usata da Streamlit/API)
├── main.py               # Entrypoint e homepage dell'app multi-pagina Streamlit
├── ollama_setup/         # <-- Configurazione per l'avvio automatico di Ollama
│   ├── Dockerfile        #   - Dockerfile personalizzato per il servizio Ollama
│   └── entrypoint.sh     #   - Script che scarica i modelli necessari all'avvio
├── pages/                # <-- Directory per le pagine dell'app Streamlit
│   ├── 1_Carica_e_Classifica.py # Pagina UI per upload e classificazione
│   └── 2_Genera_Contenuto.py    # Pagina UI per la generazione RAG
├── postgres_data_host/   # Volume Docker per la persistenza dei dati PostgreSQL
├── qdrant_data_host/     # Volume Docker per la persistenza dei dati Qdrant
├── pyproject.toml        # Definizione delle dipendenze di progetto (usato da UV/Poetry)
├── requirements.txt      # Dipendenze Python (generate da pyproject.toml)
├── README.md             # Questo file
└── src/                  # Codice sorgente dell'applicazione
    ├── api/              # Logica per gli endpoint (chiamati dalla UI)
    │   ├── __init__.py
    │   └── endpoints.py
    ├── core/
    │   ├── __init__.py
    │   └── services/     # Servizi core che gestiscono la logica di business
    │       ├── __init__.py
    │       ├── database.py       # Aggiornato: Funzioni di utility per Postgres
    │       ├── knowledge.py      # Riscritto: Gestisce il reperimento info esterne (SerpAPI)
    │       ├── llm.py            # Gestore per le interazioni con Ollama
    │       ├── models.py         # Modelli Pydantic per la validazione dei dati
    │       ├── processing.py     # Riscritto: Logica separata per classificazione e generazione
    │       └── vector_store.py   # Gestore per le interazioni con Qdrant
    └── __init__.py

---

## Nota Architetturale: Factory Pattern vs. Singleton (Gestione Event Loop)

Si potrebbe essere tentati di ottimizzare il codice usando il **Pattern Singleton** (un'istanza unica e globale) per i client dei servizi, come `OllamaService` o `VectorStoreService`, istanziandoli una sola volta a livello di modulo (es. in `agent_tools.py`).

Tuttavia, nel contesto di questa specifica applicazione (Streamlit + LangGraph + `asyncio`), questo approccio **causa un errore critico: `Event loop is closed`**.

### Spiegazione del Problema

1.  **Streamlit** e **LangGraph** (con `nest_asyncio`) gestiscono gli event loop `asyncio` in modo molto complesso e separato.
2.  Un client **asincrono** (come `OllamaService`, che usa `httpx.AsyncClient`) si "aggancia" all'event loop nel momento in cui viene creato.
3.  Se creato come Singleton (globalmente), si aggancia all'event loop principale di Streamlit.
4.  Quando un utente invia un messaggio, la chiamata al grafo (`asyncio.run(app.ainvoke(...))`) viene eseguita in un contesto di event loop diverso (o annidato).
5.  Il tentativo di usare un client (agganciato al loop A) all'interno di un'esecuzione (che gira sul loop B) porta a un conflitto e all'errore `Event loop is closed`.

### La Soluzione Adottata: Factory Pattern

Per garantire la stabilità e prevenire conflitti di loop:
* I client dei servizi (specialmente quelli `async` come `OllamaService`) **devono** essere istanziati *all'interno* delle funzioni `@tool` che li utilizzano.
* Questo approccio (noto come **Factory Pattern**) assicura che l'istanza del client (es. `ollama_cli`) viva e muoia interamente sullo stesso event loop che sta eseguendo la chiamata al tool.
* Anche se questo significa ricreare l'oggetto client a ogni chiamata, è l'architettura **più sicura e robusta** per questo specifico stack tecnologico.