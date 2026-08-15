# syntax=docker/dockerfile:1
# Contexto de build: la RAÍZ del repositorio
# Se construye así: docker build -f docker/Dockerfile -t knogment_naye .

# --------------------------------------------------------------------------
# Etapa 1: Builder (Compilación de dependencias y descarga de modelos)
# --------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ARG SPACY_MODEL=es_dep_news_trf
RUN python -m spacy download ${SPACY_MODEL}

# --------------------------------------------------------------------------
# Etapa 2: Runtime (Imagen final limpia y liviana)
# --------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    HF_HOME=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

# Copiar el código del proyecto al contenedor
COPY . /app/

RUN mkdir -p /app/db /app/.cache

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "5000"]