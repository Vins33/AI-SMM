# tests/conftest.py
"""
Pytest configuration and fixtures for testing.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


# Configure pytest-asyncio
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_db"
    settings.CHECKPOINT_PG_DSN = "postgresql://test:test@localhost:5432/test_db"
    settings.OLLAMA_BASE_URL = "http://localhost:11434"
    settings.LLM_MODEL_NAME = "test-model"
    settings.LLM_TEMPERATURE = 0.1
    settings.LLM_NUM_CTX = 4096
    settings.LLM_KEEP_ALIVE = "1h"
    settings.LLM_SEED = 42
    settings.QDRANT_HOST = "localhost"
    settings.QDRANT_PORT = 6333
    settings.EMBEDDING_MODEL_NAME = "test-embed"
    settings.SERPAPI_API_KEY = "test-api-key"
    settings.ENVIRONMENT = "test"
    settings.LOG_LEVEL = "DEBUG"
    settings.LOG_JSON_FORMAT = False
    settings.is_production = False
    settings.is_development = True
    return settings


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_qdrant_client() -> MagicMock:
    """Create a mock Qdrant client."""
    client = MagicMock()
    client.get_collections = MagicMock(return_value=MagicMock(collections=[]))
    return client


@pytest.fixture
def mock_llm() -> MagicMock:
    """Create a mock LLM."""
    llm = MagicMock()
    llm.invoke = MagicMock(return_value="Test response")
    llm.ainvoke = AsyncMock(return_value="Test response")
    return llm


@pytest.fixture
def sample_conversation_data() -> dict[str, Any]:
    """Sample conversation data for testing."""
    return {
        "id": 1,
        "title": "Test Conversation",
        "thread_id": "conv_1",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
    }


@pytest.fixture
def sample_stock_data() -> dict[str, Any]:
    """Sample stock data for testing."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": 150.0,
        "change": 2.5,
        "change_percent": 1.69,
        "market_cap": 2500000000000,
        "pe_ratio": 25.5,
        "dividend_yield": 0.5,
    }


@pytest.fixture
async def test_app(mock_settings: MagicMock) -> FastAPI:
    """Create a test FastAPI application."""
    from fastapi import FastAPI

    app = FastAPI(title="Test App")

    @app.get("/health/live")
    async def liveness():
        return {"status": "healthy"}

    @app.get("/health/ready")
    async def readiness():
        return {"status": "ready"}

    return app


@pytest.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client


# Markers
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
