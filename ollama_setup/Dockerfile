# Parti dall'immagine ufficiale di Ollama
FROM ollama/ollama:latest

# Copia lo script di avvio che abbiamo creato all'interno dell'immagine
COPY ./entrypoint.sh /entrypoint.sh

# Rendi lo script eseguibile (misura di sicurezza aggiuntiva)
RUN chmod +x /entrypoint.sh

# Imposta il nostro script come comando di avvio del container
ENTRYPOINT ["/entrypoint.sh"]