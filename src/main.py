from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.endpoints import router
from src.middleware.explainability import explainability_middleware
from src.services.database import async_engine
from src.services.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Avvio dell'applicazione in corso...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Avvio completato.")
    yield
    print("Spegnimento dell'applicazione...")

app = FastAPI(
    title="Research AI App",
    description="API per la classificazione e generazione di contenuti.",
    version="1.0.0",
    lifespan=lifespan,
)
app.middleware("http")(explainability_middleware)
app.include_router(router, prefix="/api", tags=["API"])

@app.get("/")
def read_root():
    return {"status": "ok"}
