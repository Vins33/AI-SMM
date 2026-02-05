#!/bin/bash
# Script per rilevare automaticamente l'hardware GPU disponibile
# e restituire il profilo docker-compose appropriato

detect_gpu() {
    # Controlla NVIDIA GPU (CUDA)
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            echo "cuda"
            return 0
        fi
    fi

    # Controlla AMD GPU (ROCm)
    if [ -e /dev/kfd ] && [ -e /dev/dri ]; then
        # Verifica se è una GPU AMD
        if lspci 2>/dev/null | grep -i "VGA\|3D" | grep -qi "AMD\|ATI\|Radeon"; then
            echo "rocm"
            return 0
        fi
    fi

    # Controlla se siamo su macOS (Metal - nota: Docker su Mac non supporta GPU passthrough)
    if [[ "$(uname)" == "Darwin" ]]; then
        echo "cpu"
        echo "⚠️  Nota: Su macOS, Docker non supporta GPU passthrough. Usa Ollama nativo per Metal." >&2
        return 0
    fi

    # Default: solo CPU
    echo "cpu"
    return 0
}

# Se eseguito direttamente, mostra il risultato
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    GPU_TYPE=$(detect_gpu)
    echo "🔍 Hardware rilevato: $GPU_TYPE"
    
    case $GPU_TYPE in
        cuda)
            echo "✅ NVIDIA GPU rilevata - usando profilo CUDA"
            ;;
        rocm)
            echo "✅ AMD GPU rilevata - usando profilo ROCm"
            ;;
        cpu)
            echo "ℹ️  Nessuna GPU rilevata - usando solo CPU"
            ;;
    esac
fi
