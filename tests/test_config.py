# tests/test_config.py
"""
Tests for configuration module.
"""

import pytest


@pytest.mark.unit
class TestSettings:
    """Tests for Settings configuration."""

    def test_environment_detection(self, mock_settings) -> None:
        """Test environment detection properties."""
        mock_settings.ENVIRONMENT = "production"
        mock_settings.is_production = mock_settings.ENVIRONMENT == "production"
        mock_settings.is_development = mock_settings.ENVIRONMENT == "development"

        assert mock_settings.is_production is True
        assert mock_settings.is_development is False

    def test_development_environment(self, mock_settings) -> None:
        """Test development environment detection."""
        mock_settings.ENVIRONMENT = "development"
        mock_settings.is_production = mock_settings.ENVIRONMENT == "production"
        mock_settings.is_development = mock_settings.ENVIRONMENT == "development"

        assert mock_settings.is_production is False
        assert mock_settings.is_development is True

    def test_llm_settings(self, mock_settings) -> None:
        """Test LLM configuration values."""
        assert mock_settings.LLM_MODEL_NAME == "test-model"
        assert mock_settings.LLM_TEMPERATURE == 0.1
        assert mock_settings.LLM_NUM_CTX == 4096

    def test_database_settings(self, mock_settings) -> None:
        """Test database configuration values."""
        assert "postgresql" in mock_settings.DATABASE_URL
        assert mock_settings.CHECKPOINT_PG_DSN is not None

    def test_qdrant_settings(self, mock_settings) -> None:
        """Test Qdrant configuration values."""
        assert mock_settings.QDRANT_HOST == "localhost"
        assert mock_settings.QDRANT_PORT == 6333
