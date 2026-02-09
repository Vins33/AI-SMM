# syntax=docker/dockerfile:1
# Multi-stage Dockerfile for production-ready Kubernetes deployment

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.12-slim AS production

# Labels for K8s and container registry
LABEL org.opencontainers.image.title="Financial Agent"
LABEL org.opencontainers.image.description="AI Financial Agent with LangGraph"
LABEL org.opencontainers.image.version="2.1.0"
LABEL org.opencontainers.image.authors="Vincenzo"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    # K8s/Production defaults
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    LOG_JSON_FORMAT=true

# Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup -m appuser

# Create NiceGUI storage directory with correct permissions
RUN mkdir -p /app/.nicegui && chown -R appuser:appgroup /app/.nicegui

# Point yfinance/libs cache to /dev/null (no cache at all)
ENV YF_CACHE_DIR=/dev/null
ENV XDG_CACHE_HOME=/dev/null

# Copy application code
COPY --chown=appuser:appgroup . /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check for Docker (K8s uses probes)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "src.main:fastapi_app", "--host", "0.0.0.0", "--port", "8000"]