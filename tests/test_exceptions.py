# tests/test_exceptions.py
"""
Tests for custom exception classes.
"""

import pytest

from src.core.exceptions import (
    AppError,
    DatabaseError,
    ExternalServiceError,
    LLMError,
    NotFoundError,
    ToolError,
    ValidationError,
    VectorStoreError,
)


@pytest.mark.unit
class TestAppError:
    """Tests for AppError base exception."""

    def test_basic_error(self) -> None:
        """Test basic error creation."""
        error = AppError("Test error")
        assert str(error) == "Test error"
        assert error.code == "APP_ERROR"

    def test_error_with_details(self) -> None:
        """Test error with additional details."""
        error = AppError("Test error", code="CUSTOM_CODE", details={"key": "value"})
        assert error.code == "CUSTOM_CODE"
        assert error.details == {"key": "value"}

    def test_to_dict(self) -> None:
        """Test error serialization to dict."""
        error = AppError("Test error", code="TEST_CODE")
        result = error.to_dict()

        assert result["error"] == "Test error"
        assert result["code"] == "TEST_CODE"


@pytest.mark.unit
class TestDatabaseError:
    """Tests for DatabaseError exception."""

    def test_default_code(self) -> None:
        """Test default error code."""
        error = DatabaseError("Connection failed")
        assert error.code == "DATABASE_ERROR"

    def test_inheritance(self) -> None:
        """Test that DatabaseError inherits from AppError."""
        error = DatabaseError("Test")
        assert isinstance(error, AppError)


@pytest.mark.unit
class TestLLMError:
    """Tests for LLMError exception."""

    def test_default_code(self) -> None:
        """Test default error code."""
        error = LLMError("Model not available")
        assert error.code == "LLM_ERROR"


@pytest.mark.unit
class TestVectorStoreError:
    """Tests for VectorStoreError exception."""

    def test_default_code(self) -> None:
        """Test default error code."""
        error = VectorStoreError("Collection not found")
        assert error.code == "VECTOR_STORE_ERROR"


@pytest.mark.unit
class TestToolError:
    """Tests for ToolError exception."""

    def test_default_code(self) -> None:
        """Test default error code."""
        error = ToolError("Tool execution failed")
        assert error.code == "TOOL_ERROR"


@pytest.mark.unit
class TestValidationError:
    """Tests for ValidationError exception."""

    def test_default_code(self) -> None:
        """Test default error code."""
        error = ValidationError("Invalid input")
        assert error.code == "VALIDATION_ERROR"


@pytest.mark.unit
class TestNotFoundError:
    """Tests for NotFoundError exception."""

    def test_default_code(self) -> None:
        """Test default error code."""
        error = NotFoundError("Resource not found")
        assert error.code == "NOT_FOUND"


@pytest.mark.unit
class TestExternalServiceError:
    """Tests for ExternalServiceError exception."""

    def test_default_code(self) -> None:
        """Test default error code."""
        error = ExternalServiceError("Service unavailable")
        assert error.code == "EXTERNAL_SERVICE_ERROR"

    def test_with_service_name(self) -> None:
        """Test error with service name in details."""
        error = ExternalServiceError("API timeout", details={"service": "yfinance", "timeout": 30})
        assert error.details["service"] == "yfinance"
