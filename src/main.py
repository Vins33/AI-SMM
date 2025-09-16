from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.endpoints import router

# CORRETTO: Importiamo l'engine asincrono e la Base per i modelli
from src.services.database import async_engine
from src.services.models import Base


# Definiamo un gestore del ciclo di vita 'lifespan' per l'app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Codice da eseguire all'avvio dell'applicazione
    print("Avvio dell'applicazione in corso...")
    async with async_engine.begin() as conn:
        # Crea tutte le tabelle del database (se non esistono già)
        # run_sync esegue la funzione sincrona create_all in modo sicuro nel contesto asincrono
        await conn.run_sync(Base.metadata.create_all)

    print("Avvio completato.")
    yield  # L'applicazione è in esecuzione
    # Codice da eseguire allo spegnimento dell'applicazione
    print("Spegnimento dell'applicazione...")


# Creiamo l'istanza di FastAPI e le passiamo il nostro gestore lifespan
app = FastAPI(
    title="Research AI App",
    description="API per la classificazione e generazione di contenuti.",
    version="1.0.0",
    lifespan=lifespan,
)

# Includiamo le rotte definite in endpoints.py
app.include_router(router, prefix="/api", tags=["API"])


# Aggiungiamo una rotta principale per un health check
@app.get("/")
def read_root():
    return {"status": "ok"}
