# tests/test_health.py
"""
Tests for health check endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.unit
async def test_liveness_probe(async_client: AsyncClient) -> None:
    """Test that liveness probe returns healthy status."""
    response = await async_client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_readiness_probe(async_client: AsyncClient) -> None:
    """Test that readiness probe returns ready status."""
    response = await async_client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
