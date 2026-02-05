#!/bin/bash
# Script per avviare docker-compose con auto-detection dell'hardware GPU

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Source la funzione di detection
source "$SCRIPT_DIR/detect-gpu.sh"

# Rileva il tipo di GPU
GPU_TYPE=$(detect_gpu 2>/dev/null)

echo "============================================"
echo "🚀 Avvio Classifier con auto-detection GPU"
echo "============================================"
echo ""
echo "🔍 Hardware rilevato: $GPU_TYPE"

case $GPU_TYPE in
    cuda)
        echo "✅ NVIDIA GPU rilevata - usando profilo CUDA"
        PROFILE="cuda"
        OLLAMA_SERVICE="ollama-cuda"
        ;;
    rocm)
        echo "✅ AMD GPU rilevata - usando profilo ROCm"
        PROFILE="rocm"
        OLLAMA_SERVICE="ollama-rocm"
        ;;
    cpu)
        echo "ℹ️  Nessuna GPU rilevata - usando solo CPU"
        PROFILE="cpu"
        OLLAMA_SERVICE="ollama-cpu"
        ;;
    *)
        echo "⚠️  Tipo GPU sconosciuto, uso CPU"
        PROFILE="cpu"
        OLLAMA_SERVICE="ollama-cpu"
        ;;
esac

echo ""
echo "📦 Servizio Ollama: $OLLAMA_SERVICE"
echo "============================================"
echo ""

# Passa tutti gli argomenti extra a docker compose
# Usa --profile per selezionare il servizio giusto
# Sovrascrivi il servizio ollama con quello corretto

if [ "$1" == "down" ]; then
    # Per down, ferma tutti i profili
    docker compose --profile cuda --profile rocm --profile cpu down "${@:2}"
elif [ "$1" == "logs" ]; then
    # Per logs, usa il profilo corretto
    docker compose --profile "$PROFILE" logs "${@:2}"
else
    # Per up e altri comandi
    # Crea un override per linkare il servizio ollama al servizio specifico
    docker compose --profile "$PROFILE" "$@"
fi
