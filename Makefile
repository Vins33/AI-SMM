.PHONY: help install dev test lint format build push deploy clean

# Variables
APP_NAME := financial-agent
VERSION := $(shell git describe --tags --always 2>/dev/null || echo "latest")
REGISTRY := docker.io
PYTHON := python3
UV := uv

# Colors
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

help: ## Show this help
	@echo "$(GREEN)Financial Agent - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# Development
# =============================================================================

install: ## Install production dependencies
	$(UV) sync

dev: ## Install all dependencies (including dev)
	$(UV) sync --dev

run: ## Run the application locally
	$(UV) run python -m src.main

run-reload: ## Run with hot reload for development
	$(UV) run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 \
		--reload-exclude 'postgres_data_host' \
		--reload-exclude 'qdrant_data_host' \
		--reload-exclude 'qdrant_data' \
		--reload-exclude 'ollama_data_host' \
		--reload-exclude '.venv' \
		--reload-exclude '.git'

# =============================================================================
# Testing & Quality
# =============================================================================

test: ## Run tests
	$(UV) run pytest tests/ -v

test-cov: ## Run tests with coverage
	$(UV) run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

test-unit: ## Run only unit tests
	$(UV) run pytest tests/ -v -m unit

test-integration: ## Run only integration tests
	$(UV) run pytest tests/ -v -m integration

lint: ## Run linter
	$(UV) run ruff check src/ tests/

lint-fix: ## Run linter with auto-fix
	$(UV) run ruff check src/ tests/ --fix

format: ## Format code
	$(UV) run ruff format src/ tests/

format-check: ## Check code formatting
	$(UV) run ruff format src/ tests/ --check

quality: lint format-check test ## Run all quality checks

# =============================================================================
# Docker
# =============================================================================

build: ## Build Docker image
	docker build \
		--tag $(APP_NAME):$(VERSION) \
		--tag $(APP_NAME):latest \
		--build-arg VERSION=$(VERSION) \
		--build-arg BUILD_DATE=$$(date -u +%Y-%m-%dT%H:%M:%SZ) \
		.

push: ## Push Docker image to registry
	docker tag $(APP_NAME):$(VERSION) $(REGISTRY)/$(APP_NAME):$(VERSION)
	docker push $(REGISTRY)/$(APP_NAME):$(VERSION)

docker-run: ## Run Docker container locally
	docker run --rm -it \
		--env-file .env \
		-p 8000:8000 \
		$(APP_NAME):latest

# =============================================================================
# Kubernetes
# =============================================================================

deploy-dev: ## Deploy to development environment
	./scripts/deploy.sh deploy dev

deploy-staging: ## Deploy to staging environment
	./scripts/deploy.sh deploy staging

deploy-prod: ## Deploy to production environment
	./scripts/deploy.sh deploy prod

k8s-status: ## Show Kubernetes deployment status
	./scripts/deploy.sh status

k8s-logs: ## Show Kubernetes logs
	./scripts/deploy.sh logs

rollback: ## Rollback to previous deployment
	./scripts/deploy.sh rollback

dry-run: ## Show K8s manifests without applying
	./scripts/deploy.sh dry-run

# =============================================================================
# Utilities
# =============================================================================

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

docker-clean: ## Clean Docker artifacts
	docker rmi $(APP_NAME):latest 2>/dev/null || true
	docker rmi $(APP_NAME):$(VERSION) 2>/dev/null || true
	docker system prune -f

logs: ## Show local application logs
	tail -f logs/*.log 2>/dev/null || echo "No log files found"

env: ## Show environment info
	@echo "Python: $$($(PYTHON) --version)"
	@echo "UV: $$($(UV) --version)"
	@echo "App: $(APP_NAME)"
	@echo "Version: $(VERSION)"
