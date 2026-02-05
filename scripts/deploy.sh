#!/bin/bash
# scripts/deploy.sh
# Kubernetes deployment script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="financial-agent"
REGISTRY="${REGISTRY:-docker.io}"
VERSION="${VERSION:-$(git describe --tags --always 2>/dev/null || echo 'latest')}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

show_usage() {
    echo "Usage: $0 <command> [environment]"
    echo ""
    echo "Commands:"
    echo "  build       Build Docker image"
    echo "  push        Push image to registry"
    echo "  deploy      Deploy to Kubernetes"
    echo "  rollback    Rollback to previous deployment"
    echo "  status      Show deployment status"
    echo "  logs        Show application logs"
    echo "  dry-run     Show manifests without applying"
    echo ""
    echo "Environments:"
    echo "  dev         Development environment"
    echo "  staging     Staging environment"
    echo "  prod        Production environment"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 deploy dev"
    echo "  $0 deploy prod"
    echo "  VERSION=1.0.0 $0 build"
}

check_dependencies() {
    local deps=("kubectl" "docker" "kustomize")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep is not installed"
        fi
    done
}

get_overlay_path() {
    local env=$1
    case $env in
        dev|development)
            echo "k8s/overlays/dev"
            ;;
        staging)
            echo "k8s/overlays/staging"
            ;;
        prod|production)
            echo "k8s/overlays/prod"
            ;;
        *)
            echo "k8s"  # Base
            ;;
    esac
}

build() {
    log_info "Building Docker image: ${APP_NAME}:${VERSION}"
    
    docker build \
        --tag "${APP_NAME}:${VERSION}" \
        --tag "${APP_NAME}:latest" \
        --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --build-arg VERSION="${VERSION}" \
        --build-arg VCS_REF="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" \
        --file Dockerfile \
        .
    
    log_success "Image built successfully: ${APP_NAME}:${VERSION}"
}

push() {
    local full_image="${REGISTRY}/${APP_NAME}:${VERSION}"
    
    log_info "Tagging image for registry: ${full_image}"
    docker tag "${APP_NAME}:${VERSION}" "${full_image}"
    
    log_info "Pushing image to registry..."
    docker push "${full_image}"
    
    log_success "Image pushed successfully: ${full_image}"
}

deploy() {
    local env="${1:-base}"
    local overlay_path
    overlay_path=$(get_overlay_path "$env")
    
    log_info "Deploying to environment: ${env}"
    log_info "Using overlay: ${overlay_path}"
    
    # Validate manifests
    log_info "Validating Kubernetes manifests..."
    kustomize build "${overlay_path}" | kubectl apply --dry-run=client -f -
    
    # Apply manifests
    log_info "Applying Kubernetes manifests..."
    kustomize build "${overlay_path}" | kubectl apply -f -
    
    # Wait for rollout
    local namespace
    case $env in
        dev|development) namespace="financial-agent-dev" ;;
        staging) namespace="financial-agent-staging" ;;
        *) namespace="financial-agent" ;;
    esac
    
    log_info "Waiting for rollout to complete..."
    kubectl rollout status deployment/"${APP_NAME}" -n "${namespace}" --timeout=300s
    
    log_success "Deployment completed successfully!"
}

rollback() {
    local env="${1:-base}"
    local namespace
    
    case $env in
        dev|development) namespace="financial-agent-dev" ;;
        staging) namespace="financial-agent-staging" ;;
        *) namespace="financial-agent" ;;
    esac
    
    log_warning "Rolling back deployment in namespace: ${namespace}"
    kubectl rollout undo deployment/"${APP_NAME}" -n "${namespace}"
    
    log_info "Waiting for rollback to complete..."
    kubectl rollout status deployment/"${APP_NAME}" -n "${namespace}" --timeout=300s
    
    log_success "Rollback completed successfully!"
}

status() {
    local env="${1:-base}"
    local namespace
    
    case $env in
        dev|development) namespace="financial-agent-dev" ;;
        staging) namespace="financial-agent-staging" ;;
        *) namespace="financial-agent" ;;
    esac
    
    log_info "Deployment status in namespace: ${namespace}"
    echo ""
    kubectl get deployments,pods,svc,hpa -n "${namespace}" -l "app.kubernetes.io/name=${APP_NAME}"
}

logs() {
    local env="${1:-base}"
    local namespace
    
    case $env in
        dev|development) namespace="financial-agent-dev" ;;
        staging) namespace="financial-agent-staging" ;;
        *) namespace="financial-agent" ;;
    esac
    
    log_info "Showing logs from namespace: ${namespace}"
    kubectl logs -n "${namespace}" -l "app.kubernetes.io/name=${APP_NAME}" --tail=100 -f
}

dry_run() {
    local env="${1:-base}"
    local overlay_path
    overlay_path=$(get_overlay_path "$env")
    
    log_info "Generating manifests for environment: ${env}"
    kustomize build "${overlay_path}"
}

# Main
main() {
    local command="${1:-}"
    local environment="${2:-base}"
    
    if [[ -z "$command" ]]; then
        show_usage
        exit 1
    fi
    
    check_dependencies
    
    case $command in
        build)
            build
            ;;
        push)
            push
            ;;
        deploy)
            deploy "$environment"
            ;;
        rollback)
            rollback "$environment"
            ;;
        status)
            status "$environment"
            ;;
        logs)
            logs "$environment"
            ;;
        dry-run)
            dry_run "$environment"
            ;;
        -h|--help|help)
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            ;;
    esac
}

main "$@"
