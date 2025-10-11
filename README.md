```

# Generatore di Contenuti AI (classifier)

Questo repository contiene un'applicazione Streamlit + FastAPI per classificare domande/spunti e generare contenuti (es. post per Instagram) usando LLM locali/servizi come Ollama, oltre a servizi di vettorizzazione (Qdrant) e persistenza (Postgres).

Il README originale elenca già la struttura dei file e una nota architetturale importante sull'uso di client asincroni.

Di seguito trovi una versione migliorata e più pratica del README in italiano, con istruzioni di installazione ed esecuzione locali e tramite Docker.

## Contenuti

- Descrizione breve
- Requisiti
- Installazione (locale)
- Esecuzione (locale)
- Esecuzione con Docker Compose
- Struttura del progetto
- Dettagli architetturali importanti
- Contributi e contatti

## Descrizione

Applicazione web per:

- Caricare file CSV contenenti domande/spunti
- Classificare e memorizzare le domande in un database
- Generare contenuti (post) basati sulle domande classificate
- Offrire una UI Streamlit multi-pagina (caricamento, classificazione, generazione, chat agente)

Il backend espone inoltre un'API FastAPI per l'interazione programmatica.

## Requisiti

- Python 3.12 raccomandato
- Docker & Docker Compose (opzionale, consigliato per eseguire Ollama e servizi di vettorizzazione)
- Chiavi/API opzionali: SERPAPI (se usi SerpAPI nelle impostazioni), accesso ai modelli Ollama se richiesto

## Installazione (locale)

1. Crea e attiva un virtual environment (consigliato):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Installa dipendenze:

```bash
pip install -r requirements.txt
```

3. Crea un file `.env` nella root del progetto (es. per SERPAPI_API_KEY o altre variabili). Un esempio minimo:

```env
# SERPAPI_API_KEY=your_api_key_here
```

## Esecuzione (locale)

1. Avvia l'API FastAPI (necessario se vuoi usare gli endpoint REST locali):

```bash
uvicorn src.main:app --reload --port 8000
```

2. Avvia l'interfaccia Streamlit (UI principale):

```bash
streamlit run streamlit_app.py
```

Note:
- Prima dell'avvio, assicurati che i servizi esterni (Ollama, Qdrant, Postgres) siano raggiungibili se li usi in modalità remota o tramite Docker.

## Esecuzione con Docker Compose (consigliato per ambiente integrato)

Se vuoi avviare tutto lo stack (Streamlit UI, Ollama, Postgres, Qdrant, ecc.):

```bash
docker-compose up --build
```

I servizi definiti in `docker-compose.yaml` gestiranno i volumi per Postgres e Qdrant (`postgres_data_host`, `qdrant_data_host`).

## Struttura del progetto

Le parti principali del progetto:

- `streamlit_app.py` - entrypoint dell'interfaccia Streamlit (menu e istruzioni)
- `pages/` - pagine specifiche per Streamlit (carica/classifica, genera contenuto, chat agente)
- `src/` - codice sorgente Python
  - `src/api/` - router e endpoint FastAPI
  - `src/core/services/` - servizi per DB, LLM, vettorizzazione
  - `src/services/` - (nel progetto esiste `src/services` con DB e models usati dall'API)
- `requirements.txt` - dipendenze Python
- `docker-compose.yml` e `Dockerfile` - per il deployment containerizzato

## Architettura del progetto

La seguente sezione descrive l'architettura ad alto livello, i componenti principali e come comunicano tra loro.

Componenti principali (overview):

- UI (Streamlit): pagina multi-sezione per upload, gestione dataset, classificazione e generazione dei contenuti.
- API (FastAPI): espone endpoint usati dalla UI o da client esterni per operazioni CRUD, classificazione e generazione.
- Servizi LLM (Ollama): modello locale o remoto che genera testi e risposte alle richieste di RAG.
- Vector Store (Qdrant): archivio vettoriale per retrieval e RAG.
- Database relazionale (Postgres): persistenza delle risorse strutturate (domande, metadati, storico).

Flusso semplificato delle operazioni:

1. L'utente carica un CSV tramite la UI Streamlit (`pages/1_Carica_e_Classifica.py`).
2. La UI invia i dati all'API FastAPI (`src/api/endpoints.py`) o direttamente ai servizi locali per la pre-elaborazione.
3. Il servizio di processing (`src/core/services/processing.py`) normalizza e classifica le domande; salva i risultati in Postgres (`src/core/services/database.py`) e crea embedding inviandoli al vector store (`src/core/services/vector_store.py`).
4. Quando un utente richiede generazione, la UI chiama l'API o il servizio LLM (`src/core/services/llm.py`) che può usare Ollama localmente o un servizio remoto.
5. Per RAG, il sistema esegue retrieval su Qdrant (via `vector_store.py`) e passa i contesti rilevanti al modello LLM.

Diagramma testuale dei componenti:

```
[ Streamlit UI ] <--HTTP/REST--> [ FastAPI ]
    |                             |
    |                             +--> [ Processing Service (processing.py) ]
    |                             |         |
    |                             |         +--> [ Postgres ]
    |                             |         +--> [ Qdrant Vector Store ]
    |                             |
    +--> [Pages: 1_Carica_e_Classifica, 2_Genera_Contenuto, 3_Chat]    
                              |
                              +--> [LLM: Ollama via llm.py]
```

Mappatura file -> responsabilità (sintetica):

- `streamlit_app.py` - gestione layout, navigazione e pagine Streamlit
- `pages/1_Carica_e_Classifica.py` - upload CSV, visualizzazione e trigger di classificazione
- `pages/2_Genera_Contenuto.py` - selezione elementi e generazione di post tramite LLM
- `pages/3_Chat_con_Agente_Graph.py` - chat con agente e validazione idee (se presente)
- `src/api/endpoints.py` - definizione router e endpoint REST
- `src/main.py` - avvio FastAPI e lifecycle (creazione tabelle DB)
- `src/core/services/database.py` - funzioni di accesso e gestione Postgres
- `src/core/services/processing.py` - pipeline di pulizia, classificazione e orchestrazione embedding
- `src/core/services/vector_store.py` - integrazione con Qdrant (crea/ricerca embedding)
- `src/core/services/llm.py` - interfaccia verso Ollama o provider LLM
- `ollama_setup/` - Dockerfile e script per scaricare e predisporre modelli locali

Note su deployment e scaling:

- In produzione è preferibile separare i servizi (UI, API, DB, Qdrant, Ollama) in container distinti e usare risorse dedicate.
- Il vector store (Qdrant) e Postgres devono essere persistenti (volumi Docker già previsti).
- Per carichi elevati, servire il backend FastAPI con più worker (uvicorn/gunicorn) e separare le code di elaborazione (ad es. Celery/RQ) per attività pesanti come l'embedding.

## Note architetturali importanti

1. Event loop e client asincroni

    Nell'app usiamo componenti asincroni (`httpx.AsyncClient`, `asyncpg`, ecc.). È importante non creare client asincroni globali come singole istanze condivise (Singleton) perché possono agganciarsi a un event loop specifico e causare errori tipo "Event loop is closed" quando Streamlit o LangGraph eseguono chiamate annidate. Per questo motivo il progetto adotta il Factory Pattern: i client asincroni vengono creati all'interno delle funzioni che li utilizzano e distrutti al termine della chiamata.

2. Persistenza e vettorizzazione

    - Postgres è usato per persistere dati strutturati (domande, metadati).
    - Qdrant è usato come vector store per retrieval e RAG.

3. Ollama e modelli locali

    L'integrazione con Ollama è configurata per scaricare e usare modelli locali quando possibile (vedi `ollama_setup/` con Dockerfile e `entrypoint.sh`). Questo facilita l'esecuzione offline del modello.

## Dati d'esempio

- `data/Questions.csv` è un esempio di input con domande/spunti.

Formato tipico CSV:

```csv
question_id,question_text,source
1,"Qual è l'argomento?","input"
```

## Testing rapido

1. Verifica che l'API risponda:

```bash
curl http://localhost:8000/
```

2. Apri Streamlit e testa le pagine di caricamento e generazione.

## Contributi

Se vuoi contribuire:

1. Apri una issue descrivendo il miglioramento o bug.
2. Crea una branch per la tua feature e apri una pull request.

Linee guida:
- Mantieni le dipendenze aggiornate e documenta eventuali passi di setup specifici.
- Aggiungi test minimi per la logica di business quando modifichi `src/core/services`.

## Contatti

Per domande o chiarimenti apri un'issue o inviami un messaggio nel repository.

---

Versione: aggiornata il 2025-10-11
---
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