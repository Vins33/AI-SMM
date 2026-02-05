#!/bin/bash
# scripts/deploy-ollama.sh
# Script per deployare Ollama su Kubernetes con auto-detection GPU

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Detect GPU type in Kubernetes cluster
detect_k8s_gpu() {
    # Check for NVIDIA GPU nodes
    if kubectl get nodes -o json 2>/dev/null | grep -q "nvidia.com/gpu"; then
        echo "cuda"
        return 0
    fi
    
    # Check for AMD GPU nodes
    if kubectl get nodes -o json 2>/dev/null | grep -q "amd.com/gpu"; then
        echo "rocm"
        return 0
    fi
    
    # Check for NVIDIA GPU operator
    if kubectl get pods -n gpu-operator 2>/dev/null | grep -q "nvidia"; then
        echo "cuda"
        return 0
    fi
    
    # Check node labels
    if kubectl get nodes -l accelerator=nvidia 2>/dev/null | grep -q "Ready"; then
        echo "cuda"
        return 0
    fi
    
    if kubectl get nodes -l accelerator=amd 2>/dev/null | grep -q "Ready"; then
        echo "rocm"
        return 0
    fi
    
    echo "cpu"
    return 0
}

show_usage() {
    echo "Usage: $0 [options] <command>"
    echo ""
    echo "Commands:"
    echo "  deploy [gpu-type]   Deploy Ollama (auto-detect if gpu-type not specified)"
    echo "  delete              Delete Ollama deployment"
    echo "  status              Show Ollama status"
    echo "  logs                Show Ollama logs"
    echo "  detect              Detect GPU type in cluster"
    echo ""
    echo "GPU Types:"
    echo "  cuda    NVIDIA GPU"
    echo "  rocm    AMD GPU"
    echo "  cpu     CPU only"
    echo "  auto    Auto-detect (default)"
    echo ""
    echo "Options:"
    echo "  -n, --namespace NS  Target namespace (default: financial-agent)"
    echo "  -h, --help          Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 deploy           # Auto-detect GPU and deploy"
    echo "  $0 deploy cuda      # Force NVIDIA GPU"
    echo "  $0 deploy cpu       # Force CPU only"
    echo "  $0 -n my-ns deploy  # Deploy to custom namespace"
}

NAMESPACE="financial-agent"
COMMAND=""
GPU_TYPE="auto"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        deploy|delete|status|logs|detect)
            COMMAND="$1"
            shift
            if [[ $# -gt 0 && ! "$1" =~ ^- ]]; then
                GPU_TYPE="$1"
                shift
            fi
            ;;
        cuda|rocm|cpu|auto)
            GPU_TYPE="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            ;;
    esac
done

if [[ -z "$COMMAND" ]]; then
    show_usage
    exit 1
fi

get_overlay_path() {
    local gpu_type="$1"
    echo "${PROJECT_DIR}/k8s/ollama/overlays/${gpu_type}"
}

deploy() {
    local gpu_type="$1"
    
    if [[ "$gpu_type" == "auto" ]]; then
        log_info "Auto-detecting GPU in Kubernetes cluster..."
        gpu_type=$(detect_k8s_gpu)
    fi
    
    log_info "============================================"
    log_info "🚀 Deploying Ollama to Kubernetes"
    log_info "============================================"
    log_info "GPU Type: ${gpu_type}"
    log_info "Namespace: ${NAMESPACE}"
    log_info "============================================"
    
    local overlay_path
    overlay_path=$(get_overlay_path "$gpu_type")
    
    if [[ ! -d "$overlay_path" ]]; then
        log_error "Overlay not found: $overlay_path"
    fi
    
    # Create namespace if not exists
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Ollama manifests
    log_info "Applying Ollama manifests..."
    kustomize build "$overlay_path" | kubectl apply -n "$NAMESPACE" -f -
    
    # Wait for rollout
    log_info "Waiting for Ollama to be ready..."
    kubectl rollout status deployment/ollama-${gpu_type} -n "$NAMESPACE" --timeout=300s || true
    
    log_success "Ollama deployed successfully!"
    log_info ""
    log_info "To pull models, run:"
    log_info "  kubectl exec -n ${NAMESPACE} -it deploy/ollama-${gpu_type} -- ollama pull gpt-oss:20b"
    log_info "  kubectl exec -n ${NAMESPACE} -it deploy/ollama-${gpu_type} -- ollama pull nomic-embed-text"
}

delete() {
    log_warning "Deleting all Ollama deployments in namespace: ${NAMESPACE}"
    
    for gt in cuda rocm cpu; do
        overlay_path=$(get_overlay_path "$gt")
        if [[ -d "$overlay_path" ]]; then
            kustomize build "$overlay_path" | kubectl delete -n "$NAMESPACE" -f - --ignore-not-found || true
        fi
    done
    
    log_success "Ollama deleted"
}

status() {
    log_info "Ollama status in namespace: ${NAMESPACE}"
    echo ""
    kubectl get deployments,pods,svc,pvc -n "$NAMESPACE" -l "app.kubernetes.io/name=ollama" 2>/dev/null || \
    kubectl get deployments,pods,svc,pvc -n "$NAMESPACE" -l "app.kubernetes.io/name~=ollama" 2>/dev/null || \
    kubectl get all -n "$NAMESPACE" 2>/dev/null | grep -i ollama || echo "No Ollama resources found"
}

logs() {
    log_info "Ollama logs in namespace: ${NAMESPACE}"
    kubectl logs -n "$NAMESPACE" -l "app.kubernetes.io/name=ollama" --tail=100 -f 2>/dev/null || \
    kubectl logs -n "$NAMESPACE" -l "app.kubernetes.io/component=llm" --tail=100 -f 2>/dev/null || \
    echo "No Ollama pods found"
}

detect() {
    log_info "Detecting GPU type in Kubernetes cluster..."
    local gpu_type
    gpu_type=$(detect_k8s_gpu)
    
    echo ""
    case $gpu_type in
        cuda)
            log_success "NVIDIA GPU detected - use 'cuda' profile"
            ;;
        rocm)
            log_success "AMD GPU detected - use 'rocm' profile"
            ;;
        cpu)
            log_info "No GPU detected - use 'cpu' profile"
            ;;
    esac
    echo ""
    echo "GPU_TYPE=$gpu_type"
}

# Main
case $COMMAND in
    deploy)
        deploy "$GPU_TYPE"
        ;;
    delete)
        delete
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    detect)
        detect
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        ;;
esac
