# Financial Agent - AI Chat

Applicazione web per chattare con un agente finanziario AI basato su LangGraph, con supporto per analisi di titoli, ricerca web e knowledge base vettoriale.

![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python)
![NiceGUI](https://img.shields.io/badge/Framework-NiceGUI-00A0E4?style=flat-square)
![LangGraph](https://img.shields.io/badge/Agent-LangGraph-FF6B6B?style=flat-square)
![Kubernetes](https://img.shields.io/badge/Deploy-Kubernetes-326CE5?style=flat-square&logo=kubernetes)

## Funzionalità principali

- 💬 **Chat con agente finanziario AI** (LangGraph + Ollama) con checkpointing PostgreSQL
- 📊 **Analisi fondamentale titoli** (P/E, ROE, D/E, Beta, Dividend Yield, EV/EBITDA)
- 📈 **11 Tool finanziari** (YFinance: prezzi, dividendi, news, indicatori tecnici, earnings)
- 🔍 **Ricerca web integrata** (SerpAPI/Google)
- 📚 **Knowledge Base vettoriale** (Qdrant) per memoria a lungo termine
- 💾 **Persistenza conversazioni** (PostgreSQL + LangGraph AsyncPostgresSaver)
- 🎨 **UI moderna WhatsApp-style** con NiceGUI (dark theme, angoli smussati, responsive)
- ⚙️ **Prompt configurabili** via YAML
- 🔧 **LLM configurabile** (context window, temperatura, keep-alive)
- 🚀 **Production-ready** (Kubernetes, health checks, structured logging)

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
| **Deploy** | Kubernetes (Kustomize) |

## Requisiti

- Python 3.12+
- Docker e Docker Compose
- GPU (opzionale):
  - **NVIDIA**: Driver NVIDIA + nvidia-container-toolkit (CUDA)
  - **AMD**: Driver ROCm
  - **CPU**: Funziona senza GPU (più lento)

## Installazione

### Con Docker Compose (consigliato per sviluppo)

```bash
# Clona il repository
git clone <repo-url>
cd classifier

# Crea il file .env
cp .env.example .env
# Modifica .env con le tue configurazioni

# Avvia con auto-detection GPU (consigliato)
make docker-up

# Oppure scegli manualmente:
make docker-up-cuda   # NVIDIA GPU
make docker-up-rocm   # AMD GPU
make docker-up-cpu    # Solo CPU
```

L'applicazione sarà disponibile su `http://localhost:8000`

### Sviluppo locale

```bash
# Installa dipendenze con uv
uv sync --dev

# Avvia l'applicazione
make run-reload
```

### Deploy su Kubernetes

```bash
# Build e push dell'immagine
make build
make push

# Deploy Ollama (auto-detect GPU nel cluster)
make deploy-ollama

# Oppure scegli manualmente:
make deploy-ollama-cuda   # NVIDIA GPU
make deploy-ollama-rocm   # AMD GPU
make deploy-ollama-cpu    # Solo CPU

# Deploy app (scegli ambiente)
make deploy-dev      # Development
make deploy-staging  # Staging
make deploy-prod     # Production

# Verifica status
make k8s-status
```

## Comandi disponibili

```bash
make help              # Mostra tutti i comandi disponibili
make install           # Installa dipendenze production
make dev               # Installa dipendenze dev
make test              # Esegui test
make test-cov          # Test con coverage
make lint              # Linting
make format            # Formatta codice
make quality           # Tutti i quality check
make build             # Build Docker image

# Docker Compose (locale)
make detect-gpu        # Rileva GPU disponibile
make docker-up         # Avvia con auto-detection GPU
make docker-up-cuda    # Avvia con NVIDIA GPU
make docker-up-rocm    # Avvia con AMD GPU
make docker-up-cpu     # Avvia solo CPU
make docker-down       # Ferma tutti i servizi

# Kubernetes
make deploy-ollama     # Deploy Ollama (auto-detect GPU)
make deploy-ollama-cuda
make deploy-ollama-rocm
make deploy-ollama-cpu
make delete-ollama     # Elimina Ollama da K8s
make k8s-detect-gpu    # Rileva GPU nel cluster K8s
make deploy-dev        # Deploy app su K8s dev
make deploy-prod       # Deploy app su K8s prod
```

## Test Kubernetes locale con Kind

Per testare il deploy Kubernetes in locale, puoi usare [Kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker):

### Installazione Kind e kubectl

```bash
# Installa Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Installa kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### Creazione cluster e deploy

```bash
# Crea cluster Kind
kind create cluster --config kind-config.yaml

# Build e carica l'immagine nel cluster
docker build -t classifier-app:latest .
kind load docker-image classifier-app:latest --name financial-agent-local

# Deploy all-in-one (app + postgres + qdrant + ollama CPU)
kubectl apply -f k8s/local/all-in-one.yaml

# Per GPU support, usa lo script dedicato:
./scripts/deploy-ollama.sh deploy cuda   # NVIDIA
./scripts/deploy-ollama.sh deploy rocm   # AMD
./scripts/deploy-ollama.sh deploy cpu    # CPU only
./scripts/deploy-ollama.sh deploy        # Auto-detect

# Verifica pods
kubectl get pods -n financial-agent-local

# Accedi all'applicazione via port-forward
kubectl port-forward -n financial-agent-local svc/financial-agent 8888:80
# Apri http://localhost:8888
```

### Pull modelli su Ollama in K8s

```bash
# Connettiti al pod Ollama e scarica i modelli
kubectl exec -n financial-agent-local -it deploy/ollama -- ollama pull gpt-oss:20b
kubectl exec -n financial-agent-local -it deploy/ollama -- ollama pull nomic-embed-text
```

### Test health checks

```bash
curl http://localhost:8888/health/live   # Liveness probe
curl http://localhost:8888/health/ready  # Readiness probe
```

### Comandi utili

```bash
# Logs dell'applicazione
kubectl logs -n financial-agent-local -l app=financial-agent -f

# Stato di tutti i componenti
kubectl get all -n financial-agent-local

# Descrivi un pod (per debug)
kubectl describe pod -n financial-agent-local -l app=financial-agent

# Elimina il cluster quando hai finito
kind delete cluster --name financial-agent-local
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
| ollama-cuda | 11434 | LLM con NVIDIA GPU |
| ollama-rocm | 11434 | LLM con AMD GPU |
| ollama-cpu | 11434 | LLM solo CPU |
| qdrant | 6333, 6334 | Vector database |
| postgres_db | 5432 | Database relazionale |

## GPU Auto-Detection

Il sistema rileva automaticamente la GPU disponibile:

### Docker Compose
```bash
# Rileva GPU locale
./scripts/detect-gpu.sh

# Output possibili:
# 🔍 Hardware rilevato: cuda   (NVIDIA)
# 🔍 Hardware rilevato: rocm   (AMD)
# 🔍 Hardware rilevato: cpu    (nessuna GPU)

# Avvia con detection automatica
make docker-up
```

### Kubernetes
```bash
# Rileva GPU nel cluster K8s
./scripts/deploy-ollama.sh detect

# Deploy con auto-detection
./scripts/deploy-ollama.sh deploy

# O specifica manualmente
./scripts/deploy-ollama.sh deploy cuda
./scripts/deploy-ollama.sh deploy rocm
./scripts/deploy-ollama.sh deploy cpu
```

### Struttura K8s per Ollama

```
k8s/ollama/
├── base/                    # Configurazione base
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── pvc.yaml
│   └── kustomization.yaml
└── overlays/
    ├── cuda/               # NVIDIA GPU
    │   └── kustomization.yaml
    ├── rocm/               # AMD GPU
    │   └── kustomization.yaml
    └── cpu/                # CPU only
        └── kustomization.yaml
```

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

**Versione**: 2.1.1  
**Ultimo aggiornamento**: 2026-02-05  
**Autore**: Vincenzo