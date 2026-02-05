# Agente Finanziario - Chat

Applicazione web per chattare con un agente finanziario AI basato su LangGraph, con supporto per analisi di titoli, ricerca web e knowledge base vettoriale.

![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python)
![NiceGUI](https://img.shields.io/badge/Framework-NiceGUI-00A0E4?style=flat-square)
![LangGraph](https://img.shields.io/badge/Agent-LangGraph-FF6B6B?style=flat-square)

## Funzionalità principali

- 💬 **Chat con agente finanziario AI** (LangGraph + Ollama) con checkpointing PostgreSQL
- 📊 **Analisi fondamentale titoli** (P/E, ROE, D/E, Beta, Dividend Yield, EV/EBITDA)
- 🔍 **Ricerca web integrata** (SerpAPI/Google)
- 📚 **Knowledge Base vettoriale** (Qdrant) per memoria a lungo termine
- 💾 **Persistenza conversazioni** (PostgreSQL + LangGraph AsyncPostgresSaver)
- 🎨 **UI moderna WhatsApp-style** con NiceGUI (dark theme, angoli smussati, responsive)
- ⚙️ **Prompt configurabili** via YAML
- 🔧 **LLM configurabile** (context window, temperatura, keep-alive)

## Screenshot

L'interfaccia è ispirata a WhatsApp con:
- Sidebar con lista conversazioni e ricerca
- Header con avatar e stato online
- Bolle messaggi arrotondate con colori distinti
- Input floating centrato
- Tabelle markdown con angoli smussati

## Stack tecnologico

| Componente | Tecnologia |
|------------|------------|
| **Frontend** | NiceGUI 3.6+ (async, integrato con FastAPI) |
| **Backend** | FastAPI (async) |
| **Database** | PostgreSQL 16 + SQLAlchemy 2.0 (async + asyncpg) |
| **Vector Store** | Qdrant |
| **LLM** | Ollama (locale) - modello: gpt-oss:20b |
| **Agent Framework** | LangGraph + LangChain |
| **Checkpointing** | LangGraph AsyncPostgresSaver |

## Requisiti

- Python 3.12+
- Docker e Docker Compose
- GPU NVIDIA (consigliato per Ollama)

## Installazione

### Con Docker Compose (consigliato)

```bash
# Clona il repository
git clone <repo-url>
cd classifier

# Crea il file .env
cp .env.exemple .env
# Modifica .env con le tue configurazioni

# Avvia tutti i servizi
docker compose up --build
```

L'applicazione sarà disponibile su `http://localhost:8000`

### Sviluppo locale

```bash
# Crea ambiente virtuale con uv
uv venv
source .venv/bin/activate

# Installa dipendenze
uv pip install -r requirements.txt

# Avvia l'applicazione
python -m uvicorn src.main:fastapi_app --host 0.0.0.0 --port 8000 --reload
```

## Struttura del progetto

```
classifier/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point FastAPI + NiceGUI
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py        # REST API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configurazione LLM e app (pydantic-settings)
│   │   ├── prompts.py          # Loader prompts da YAML
│   │   ├── prompts.yaml        # Tutti i prompts configurabili
│   │   ├── agent_graph.py      # LangGraph agent con checkpointing
│   │   └── agent_tools.py      # Tool LangChain (web, kb, stocks)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy async + CRUD
│   │   ├── financial.py        # Analisi titoli (yfinance)
│   │   ├── knowledge.py        # Ricerca web (SerpAPI)
│   │   ├── llm.py              # Servizio Ollama
│   │   ├── models.py           # Modelli SQLAlchemy (Conversation, Message)
│   │   └── vector_store.py     # Servizio Qdrant
│   └── ui/
│       ├── __init__.py
│       ├── app.py              # NiceGUI app entry
│       ├── components/
│       │   ├── __init__.py
│       │   ├── chat.py         # ChatMessage, ChatInput, ChatContainer
│       │   └── sidebar.py      # ConversationList con rename/delete
│       └── pages/
│           ├── __init__.py
│           └── chat_page.py    # Pagina chat principale
├── data/                       # Dati esempio
├── ollama_setup/               # Setup Ollama Docker
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── pyproject.toml
└── .env
└── .env
```

## Configurazione

### Variabili ambiente (.env)

```env
# PostgreSQL
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=instagram_content_db
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres_db:5432/${POSTGRES_DB}

# Servizi
OLLAMA_BASE_URL=http://ollama:11434
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Modelli
EMBEDDING_MODEL_NAME=nomic-embed-text
LLM_MODEL_NAME=gpt-oss:20b

# API Keys
SERPAPI_API_KEY=your_api_key_here
```

### Configurazione LLM (src/core/config.py)

```python
# Context window (importante per memoria conversazione)
LLM_NUM_CTX = 16384  # Default: 16K tokens

# Temperatura (creatività)
LLM_TEMPERATURE = 0.1  # Bassa per risposte precise

# Keep-alive modello in memoria
LLM_KEEP_ALIVE = "4h"
```

### Configurazione Prompts (src/core/prompts.yaml)

Tutti i prompt dell'agente sono configurabili via YAML:

```yaml
agent:
  system_prompt: |
    Sei un assistente finanziario esperto...

tools:
  web_search:
    description: "Cerca informazioni aggiornate sul web..."
  stock_scoring:
    description: "Analizza un titolo azionario..."
```

## Architettura

### Flusso delle richieste

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NiceGUI UI    │────▶│    FastAPI      │────▶│   LangGraph     │
│   (Browser)     │◀────│    Backend      │◀────│   Agent         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   PostgreSQL    │     │   Tool Chain    │
                        │   (Sessions)    │     │                 │
                        └─────────────────┘     ├─────────────────┤
                                                │ • web_search    │
                                                │ • read_kb       │
                                                │ • write_kb      │
                                                │ • stock_scoring │
                                                └─────────────────┘
                                                        │
                                        ┌───────────────┼───────────────┐
                                        ▼               ▼               ▼
                                 ┌───────────┐  ┌───────────┐  ┌───────────┐
                                 │  SerpAPI  │  │  Qdrant   │  │  yfinance │
                                 │  (Web)    │  │  (Vector) │  │  (Stocks) │
                                 └───────────┘  └───────────┘  └───────────┘
```

### Tool disponibili

| Tool | Descrizione | Utilizzo |
|------|-------------|----------|
| `web_search_tool` | Ricerca Google via SerpAPI | Notizie recenti, eventi |
| `read_from_kb_tool` | Lettura da Knowledge Base | Info concettuali, procedure |
| `write_to_kb_tool` | Scrittura su Knowledge Base | Definizioni, linee guida |
| `stock_scoring_tool` | Analisi fondamentale titoli | Score BUY/HOLD/SELL |

### Pattern architetturali

- **Async-first**: Tutto il codice è asincrono (asyncio, SQLAlchemy async)
- **Factory Pattern**: I client async vengono creati dentro le funzioni per evitare conflitti di event loop
- **Clean Architecture**: Separazione tra UI, API, servizi e core business logic
- **Dependency Injection**: FastAPI Depends per gestione sessioni DB

## API Endpoints

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/conversations/` | Lista conversazioni |
| POST | `/api/conversations/` | Nuova conversazione |
| GET | `/api/conversations/{id}/messages/` | Messaggi conversazione |
| POST | `/api/conversations/{id}/messages/` | Nuovo messaggio |

## Sviluppo

### Aggiungere dipendenze

```bash
uv pip install <package>
uv pip freeze > requirements.txt
```

### Linting

```bash
ruff check src/
ruff format src/
```

### Test

```bash
pytest tests/
```

## Docker Services

| Servizio | Porta | Descrizione |
|----------|-------|-------------|
| app | 8000 | FastAPI + NiceGUI |
| ollama | 11434 | LLM locale |
| qdrant | 6333, 6334 | Vector database |
| postgres_db | 5432 | Database relazionale |

## Contributi

1. Apri una issue descrivendo il miglioramento o bug
2. Crea una branch per la tua feature
3. Apri una pull request

## Licenza

**Non-Commercial License (CC BY-NC 4.0)**

Questo software è rilasciato sotto licenza Creative Commons Attribution-NonCommercial 4.0 International.

✅ **Permesso**:
- Uso personale e educativo
- Modifica e redistribuzione (con attribuzione)
- Uso in progetti di ricerca non commerciali

❌ **Vietato**:
- Uso commerciale o a scopo di lucro
- Vendita del software o derivati
- Integrazione in prodotti/servizi commerciali

Per uso commerciale, contattare l'autore per una licenza separata.

Maggiori info: https://creativecommons.org/licenses/by-nc/4.0/

---

**Versione**: 2.1.0  
**Ultimo aggiornamento**: 2026-02-05  
**Autore**: Vincenzo