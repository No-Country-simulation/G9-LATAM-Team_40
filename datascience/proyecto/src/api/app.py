"""Servidor FastAPI principal y simplificado."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from settings import settings
from indexacion.main import PipelineGraphRAG
from .schemas import QueryRequest, QueryResponse

logger = logging.getLogger("API")

# Instancia global en memoria para no recargar el grafo en cada request
rag_pipeline: PipelineGraphRAG | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga los modelos en memoria una sola vez al arrancar."""
    global rag_pipeline
    settings.ensure_dirs()
    settings.validate_keys()
    
    logger.info("Cargando Pipeline GraphRAG en memoria...")
    rag_pipeline = PipelineGraphRAG()
    yield
    logger.info("Servidor apagado.")


app = FastAPI(
    title="KNOGMENT_NAYE - GraphRAG API",
    version="1.0.0",
    lifespan=lifespan
)

# Permitir consumo desde el frontend o clientes externos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Estado del servidor y verificación de modelo cargado."""
    return {
        "status": "ok", 
        "model_loaded": rag_pipeline is not None
    }


@app.post("/api/v1/query", response_model=QueryResponse)
def responder_pregunta(payload: QueryRequest):
    """Endpoint principal de consulta GraphRAG."""
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="El modelo GraphRAG aún no está inicializado.")

    try:
        t0 = time.time()
        respuesta_texto = rag_pipeline.ejecutar_consulta(payload.pregunta)
        t1 = time.time()

        return QueryResponse(
            pregunta=payload.pregunta,
            respuesta=respuesta_texto,
            tiempo_segundos=round(t1 - t0, 2)
        )
    except Exception as e:
        logger.error("Error al procesar la consulta: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=5000, reload=True)