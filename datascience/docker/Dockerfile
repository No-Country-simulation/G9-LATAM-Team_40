# syntax=docker/dockerfile:1
# Contexto de build: la RAÍZ del repositorio (KNOGMENT_NAYE/ o knogment_naye_v2/)
# Se construye así: docker build -f docker/Dockerfile -t knogment_naye .

# --------------------------------------------------------------------------
# Etapa 1: Builder (Compilación de dependencias y descarga de modelos)
# --------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Herramientas necesarias solo para compilar dependencias C/C++ (Faiss, SpaCy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Crear entorno virtual aislado para copiar a runtime
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar e instalar dependencias de Python
COPY proyecto/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Descargar el modelo Transformer de spaCy alineado a settings.py (es_dep_news_trf)
ARG SPACY_MODEL=es_dep_news_trf
RUN python -m spacy download ${SPACY_MODEL}


# --------------------------------------------------------------------------
# Etapa 2: Runtime (Imagen final limpia y liviana)
# --------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/proyecto/src:/app/proyecto" \
    HF_HOME=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

# Dependencias mínimas de ejecución (curl para Healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar entorno virtual compilado desde el builder (sin herramientas de compilación C++)
COPY --from=builder /opt/venv /opt/venv

# Copiar código del proyecto
COPY proyecto/ ./proyecto/

# Crear directorios para persistencia de datos y caché de modelos
RUN mkdir -p /app/db /app/.cache

# Seguridad: Crear usuario no-root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

WORKDIR /app/proyecto

# Puerto expuesto para la API FastAPI
EXPOSE 8000

# Comando por defecto: Levanta la API REST FastAPI
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "5000"]