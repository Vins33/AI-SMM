# src/api/health.py
"""Health check endpoints for Kubernetes liveness/readiness probes."""

import asyncio
from datetime import datetime, timezone
from enum import Enum

import httpx
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from src.core.config import settings
from src.core.logging import get_logger
from src.services.database import async_engine

logger = get_logger("health")

router = APIRouter(tags=["Health"])


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ComponentHealth(BaseModel):
    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None


class HealthResponse(BaseModel):
    status: HealthStatus
    version: str
    environment: str
    timestamp: str
    components: dict[str, ComponentHealth]


async def check_database() -> ComponentHealth:
    """Check PostgreSQL connection."""
    start = asyncio.get_event_loop().time()
    try:
        async with async_engine.connect() as conn:
            await asyncio.wait_for(
                conn.execute(text("SELECT 1")),
                timeout=settings.HEALTH_CHECK_TIMEOUT,
            )
        latency = (asyncio.get_event_loop().time() - start) * 1000
        return ComponentHealth(status=HealthStatus.HEALTHY, latency_ms=round(latency, 2))
    except asyncio.TimeoutError:
        return ComponentHealth(status=HealthStatus.UNHEALTHY, message="Database timeout")
    except Exception as e:
        logger.error("Database health check failed", extra={"error": str(e)})
        return ComponentHealth(status=HealthStatus.UNHEALTHY, message=str(e))


async def check_ollama() -> ComponentHealth:
    """Check Ollama LLM service."""
    start = asyncio.get_event_loop().time()
    try:
        async with httpx.AsyncClient(timeout=settings.HEALTH_CHECK_TIMEOUT) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            latency = (asyncio.get_event_loop().time() - start) * 1000
            if response.status_code == 200:
                return ComponentHealth(status=HealthStatus.HEALTHY, latency_ms=round(latency, 2))
            return ComponentHealth(
                status=HealthStatus.DEGRADED,
                latency_ms=round(latency, 2),
                message=f"Status {response.status_code}",
            )
    except asyncio.TimeoutError:
        return ComponentHealth(status=HealthStatus.UNHEALTHY, message="Ollama timeout")
    except Exception as e:
        logger.warning("Ollama health check failed", extra={"error": str(e)})
        return ComponentHealth(status=HealthStatus.DEGRADED, message=str(e))


async def check_qdrant() -> ComponentHealth:
    """Check Qdrant vector store."""
    start = asyncio.get_event_loop().time()
    try:
        async with httpx.AsyncClient(timeout=settings.HEALTH_CHECK_TIMEOUT) as client:
            response = await client.get(f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/readyz")
            latency = (asyncio.get_event_loop().time() - start) * 1000
            if response.status_code == 200:
                return ComponentHealth(status=HealthStatus.HEALTHY, latency_ms=round(latency, 2))
            return ComponentHealth(
                status=HealthStatus.DEGRADED,
                latency_ms=round(latency, 2),
                message=f"Status {response.status_code}",
            )
    except asyncio.TimeoutError:
        return ComponentHealth(status=HealthStatus.UNHEALTHY, message="Qdrant timeout")
    except Exception as e:
        logger.warning("Qdrant health check failed", extra={"error": str(e)})
        return ComponentHealth(status=HealthStatus.DEGRADED, message=str(e))


@router.get("/health/live", response_model=dict[str, str])
async def liveness_probe():
    """
    Kubernetes liveness probe.
    Returns 200 if the application is running.
    Failure triggers pod restart.
    """
    return {"status": "alive"}


@router.get("/health/ready", response_model=dict[str, str])
async def readiness_probe(response: Response):
    """
    Kubernetes readiness probe.
    Returns 200 if the application can accept traffic.
    Failure removes pod from service endpoints.
    """
    db_health = await check_database()

    if db_health.status == HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready", "reason": "database unavailable"}

    return {"status": "ready"}


@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response):
    """
    Comprehensive health check for monitoring dashboards.
    Returns status of all components.
    """
    # Run all checks in parallel
    db_health, ollama_health, qdrant_health = await asyncio.gather(
        check_database(),
        check_ollama(),
        check_qdrant(),
    )

    components = {
        "database": db_health,
        "ollama": ollama_health,
        "qdrant": qdrant_health,
    }

    # Determine overall status
    statuses = [c.status for c in components.values()]

    if all(s == HealthStatus.HEALTHY for s in statuses):
        overall_status = HealthStatus.HEALTHY
    elif any(s == HealthStatus.UNHEALTHY for s in statuses):
        overall_status = HealthStatus.UNHEALTHY
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        overall_status = HealthStatus.DEGRADED

    return HealthResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        components=components,
    )


@router.get("/health/startup")
async def startup_probe(response: Response):
    """
    Kubernetes startup probe.
    Returns 200 once the application has fully started.
    """
    db_health = await check_database()

    if db_health.status == HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "starting", "reason": "waiting for database"}

    return {"status": "started"}
