# in Dockerfile

FROM python:3.12-slim

WORKDIR /app

# Imposta le variabili d'ambiente per Python
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Installa le dipendenze di sistema (necessarie per psycopg2-binary, ecc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia i requisiti e installa le dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice sorgente
COPY . /app

# Espone le porte che useranno i servizi (FastAPI e Streamlit)
EXPOSE 8000
EXPOSE 8501

# Comando di default (sarà sovrascritto da docker-compose)
CMD ["python", "src/main.py"]