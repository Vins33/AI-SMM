# src/core/exceptions.py
"""Custom exceptions and error handling for the application."""

from typing import Any


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class DatabaseError(AppError):
    """Database operation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=503,
            details=details,
        )


class LLMError(AppError):
    """LLM service error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="LLM_ERROR",
            status_code=503,
            details=details,
        )


class VectorStoreError(AppError):
    """Vector store error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="VECTOR_STORE_ERROR",
            status_code=503,
            details=details,
        )


class ToolError(AppError):
    """Tool execution error."""

    def __init__(self, tool_name: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="TOOL_ERROR",
            status_code=500,
            details={"tool": tool_name, **(details or {})},
        )


class ValidationError(AppError):
    """Input validation error."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field} if field else {},
        )


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            message=f"{resource} not found",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "id": resource_id},
        )


class ExternalServiceError(AppError):
    """External service error (API, etc.)."""

    def __init__(self, service: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service, **(details or {})},
        )
