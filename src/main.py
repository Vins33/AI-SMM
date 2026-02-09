# src/main.py
"""Application entry point - FastAPI backend with NiceGUI frontend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from nicegui import app as nicegui_app
from nicegui import ui

from src.api.admin import router as admin_router
from src.api.auth import router as auth_router
from src.api.endpoints import router
from src.api.health import router as health_router
from src.core.config import settings
from src.core.exceptions import AppError
from src.core.logging import get_logger, setup_logging
from src.services.database import init_db
from src.ui.pages.admin_page import AdminDashboard
from src.ui.pages.chat_page import ChatPage
from src.ui.pages.login_page import LoginPage, RegisterPage
from src.ui.pages.profile_page import ProfilePage

# Setup logging first
setup_logging(
    level=settings.LOG_LEVEL,
    json_format=settings.LOG_JSON_FORMAT,
    app_name=settings.APP_NAME,
)

logger = get_logger("main")


@asynccontextmanager
async def lifespan(fastapi_application: FastAPI):
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
fastapi_app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
fastapi_app.include_router(admin_router, prefix="/api/v1", tags=["Admin"])
fastapi_app.include_router(router, prefix="/api/v1", tags=["API"])


# NiceGUI pages
@ui.page("/")
async def index():
    """Main chat page - requires authentication."""
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

    # Check if user is authenticated
    token = nicegui_app.storage.user.get("access_token", "")
    if not token:
        ui.navigate.to("/login")
        return

    # Extract user_id from storage for conversation segregation
    user_id = nicegui_app.storage.user.get("user_id")
    role = nicegui_app.storage.user.get("role", "user")

    chat_page = ChatPage(is_dark=True, user_id=user_id, role=role)
    await chat_page.render()


@ui.page("/login")
async def login_page():
    """Login page."""
    # Don't auto-redirect - let user explicitly navigate after login
    login = LoginPage(is_dark=True)
    await login.render()


@ui.page("/register")
async def register_page():
    """Registration page."""
    # Don't auto-redirect - let user explicitly navigate
    register = RegisterPage(is_dark=True)
    await register.render()


@ui.page("/profile")
async def profile_page():
    """User profile and insights page."""
    token = nicegui_app.storage.user.get("access_token", "")
    if not token:
        ui.navigate.to("/login")
        return
    profile = ProfilePage(is_dark=True)
    await profile.render()


@ui.page("/admin")
async def admin_page():
    """Admin dashboard page."""
    admin = AdminDashboard(is_dark=True)
    await admin.render()


@ui.page("/verify-email")
async def verify_email_page(token: str = ""):
    """Email verification landing page."""
    ui.dark_mode(True)
    ui.add_head_html(
        """
        <style>
            body { margin: 0; padding: 0; background-color: #0b141a; }
            .nicegui-content { height: 100vh; display: flex; justify-content: center; align-items: center; }
        </style>
        """
    )

    with ui.card().classes("w-96 p-8 bg-[#202c33] rounded-2xl shadow-2xl text-center"):
        if not token:
            ui.icon("error").classes("text-6xl text-red-400 mb-4 mx-auto")
            ui.label("Link non valido").classes("text-xl font-bold text-white mb-2")
            ui.label("Il link di verifica non contiene un token valido.").classes(
                "text-gray-400 text-sm mb-4"
            )
        else:
            # Call the API to verify
            import httpx

            try:
                async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
                    response = await client.get(
                        f"/api/v1/auth/verify-email?token={token}"
                    )

                if response.status_code == 200:
                    ui.icon("check_circle").classes("text-6xl text-green-400 mb-4 mx-auto")
                    ui.label("Email Verificata!").classes("text-xl font-bold text-white mb-2")
                    ui.label("Il tuo indirizzo email è stato verificato con successo.").classes(
                        "text-gray-400 text-sm mb-4"
                    )
                    # Update session storage if user is logged in
                    if nicegui_app.storage.user.get("access_token"):
                        nicegui_app.storage.user["email_verified"] = True
                else:
                    error_detail = "Errore nella verifica"
                    try:
                        error_detail = response.json().get("detail", error_detail)
                    except Exception:
                        pass
                    ui.icon("error").classes("text-6xl text-red-400 mb-4 mx-auto")
                    ui.label("Verifica fallita").classes("text-xl font-bold text-white mb-2")
                    ui.label(error_detail).classes("text-gray-400 text-sm mb-4")
            except Exception as e:
                ui.icon("error").classes("text-6xl text-red-400 mb-4 mx-auto")
                ui.label("Errore").classes("text-xl font-bold text-white mb-2")
                ui.label(f"Errore di connessione: {e}").classes("text-gray-400 text-sm mb-4")

        ui.button(
            "Vai alla Chat",
            on_click=lambda: ui.navigate.to("/"),
        ).classes(
            "w-full bg-gradient-to-r from-green-500 to-teal-600 text-white py-3 "
            "rounded-lg font-semibold hover:from-green-600 hover:to-teal-700 mt-2"
        )


@ui.page("/logout")
async def logout_page():
    """Logout: blacklist token server-side and clear client session."""
    try:
        import httpx

        token = nicegui_app.storage.user.get("access_token", "")
        if token:
            async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
                await client.post(
                    "/api/v1/auth/logout",
                    headers={"Authorization": f"Bearer {token}"},
                )
        nicegui_app.storage.user.clear()
    except Exception:
        nicegui_app.storage.user.clear()
    ui.navigate.to("/login")


# Initialize NiceGUI with FastAPI
ui.run_with(
    fastapi_app,
    title="Agente Finanziario",
    storage_secret=settings.STORAGE_SECRET,
)

# Alias for uvicorn compatibility (uvicorn src.main:app)
app = fastapi_app
