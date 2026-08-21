# syntax=docker/dockerfile:1
# Contexto de build: la RAÍZ del repositorio (NAYELI_V2/)
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

# requirements.txt está dentro de proyecto/, no en la raíz del contexto.
COPY proyecto/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Modelo transformer de spaCy en español (el más pesado/preciso). Si el
# contenedor corre sin GPU, es_core_news_lg es una alternativa más liviana.
ARG SPACY_MODEL=es_dep_news_trf
RUN python -m spacy download ${SPACY_MODEL}

# --------------------------------------------------------------------------
# Etapa 2: Runtime (Imagen final limpia y liviana)
# --------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

# PYTHONPATH necesita DOS entradas:
# - /app       -> para importar "src" como paquete (CMD: src.api.app:app)
# - /app/src   -> settings.py vive DENTRO de src/, y varios módulos
#                 (pipeline.py, graph_builder.py, indice_grafo.py, etc.)
#                 hacen "from settings import settings" como import plano/
#                 absoluto, que solo resuelve si /app/src está en el path.
#
# ROOT_DIR=/app: en local, settings.py calcula ROOT_DIR con 3 niveles hacia
# arriba (proyecto/src/settings.py -> src -> proyecto -> NAYELI_V2, donde
# está db/). Pero acá abajo aplanamos proyecto/ directo a /app/, así que esa
# cuenta de 3 niveles ya no aplica (subiría por encima de /app). Como
# ROOT_DIR es un Field de Pydantic Settings, esta variable de entorno tiene
# prioridad sobre el cálculo automático del archivo.
ENV PYTHONPATH="/app:/app/src" \
    ROOT_DIR=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Trae el venv ya armado (dependencias + modelo spaCy) desde la etapa builder.
COPY --from=builder /opt/venv /opt/venv

# Se copia el código y los recursos del proyecto sin ningún archivo `.env`.
# Las variables de configuración llegan únicamente desde el proceso de
# Docker Compose; el contenedor no crea ni monta un `.env` dentro de `/app`.
COPY proyecto/ /app/

# db/ se sobreescribe por volumen en docker-compose, pero se crea igual por
# si el contenedor corre suelto (sin compose) sin ese volumen.
RUN mkdir -p /app/db /app/.cache

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "5000"]