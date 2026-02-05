# src/main.py
"""Application entry point - FastAPI backend with NiceGUI frontend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from nicegui import ui

from src.api.endpoints import router
from src.api.health import router as health_router
from src.core.config import settings
from src.core.exceptions import AppError
from src.core.logging import get_logger, setup_logging
from src.services.database import init_db
from src.ui.pages.chat_page import ChatPage

# Setup logging first
setup_logging(
    level=settings.LOG_LEVEL,
    json_format=settings.LOG_JSON_FORMAT,
    app_name=settings.APP_NAME,
)

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(
        "Starting application",
        extra={
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        },
    )
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down application")


# Create FastAPI app
fastapi_app = FastAPI(
    title="Financial Agent API",
    description="API for financial agent with LangGraph.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)


# Global exception handler
@fastapi_app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handle custom application errors."""
    logger.error(
        exc.message,
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
        },
    )
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@fastapi_app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.exception(
        "Unhandled exception",
        extra={"path": request.url.path, "error": str(exc)},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )


# Include routers
fastapi_app.include_router(health_router)
fastapi_app.include_router(router, prefix="/api/v1", tags=["API"])


# NiceGUI pages
@ui.page("/")
async def index():
    """Main chat page."""
    # Enable dark mode for ChatGPT-like appearance
    ui.dark_mode(True)
    ui.add_head_html(
        """
        <style>
            body { margin: 0; padding: 0; background-color: #343541; }
            .nicegui-content { height: 100vh; }
            .q-textarea .q-field__control { background: transparent !important; }
            .q-textarea textarea { color: white !important; }
            .q-textarea .q-placeholder { color: #8e8ea0 !important; }
        </style>
        """
    )
    chat_page = ChatPage(is_dark=True)
    await chat_page.render()


# Initialize NiceGUI with FastAPI
ui.run_with(
    fastapi_app,
    title="Agente Finanziario",
    storage_secret="financial-agent-secret",
)

# Alias for uvicorn compatibility (uvicorn src.main:app)
app = fastapi_app
