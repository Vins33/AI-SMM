#!/bin/bash
set -e

# Avvia il server Ollama in background
ollama serve &

# Salva il Process ID (PID) del server
PID=$!

echo "Server Ollama avviato in background con PID: $PID"
sleep 5 # Attendi qualche secondo per essere sicuro che il server sia pronto

echo "Inizio il download dei modelli (verrà eseguito solo se non sono già presenti)..."

# Scarica i modelli necessari
ollama pull gpt-oss:20b
ollama pull nomic-embed-text

echo "Download dei modelli completato. gpt-oss:20b, nomic-embed-text"

# Riporta il processo del server in primo piano per mantenere il container attivo
wait $PID