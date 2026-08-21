"""
Servidor FastAPI para la interfaz GraphRAG.
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from settings import settings
from storage.oci_object_storage import sync_metadata_from_oci
from indexacion.main import PipelineGraphRAG
from .schemas import QueryRequest, QueryResponse

logger = logging.getLogger("API")

# Instancia global en memoria
rag_pipeline: PipelineGraphRAG | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga los modelos en memoria una sola vez al arrancar.

    IMPORTANTE: aquí solo se sincronizan el grafo y los embeddings (livianos).
    Los .secciones.json de cada documento NO se descargan aquí — se resuelven
    bajo demanda dentro de IndiceGrafo, solo cuando un documento_id específico
    aparece en la trazabilidad de una consulta real (ver indice_grafo.py).
    """
    global rag_pipeline
    settings.ensure_dirs()

    if settings.DATA_SOURCE.lower() == "oci" and settings.OCI_SYNC_ON_STARTUP:
        logger.info("Sincronizando grafo + embeddings desde OCI Object Storage antes de iniciar la API...")
        sync_metadata_from_oci(settings)
        logger.info("Metadata sincronizada. Los documentos (.secciones.json) se resolverán bajo demanda por consulta.")

    logger.info("Cargando Pipeline GraphRAG en memoria...")
    try:
        rag_pipeline = PipelineGraphRAG()
        logger.info("Pipeline cargado exitosamente.")
    except Exception as e:
        logger.error("Error crítico al inicializar el pipeline: %s", e)
        raise e

    yield
    logger.info("Servidor apagado.")


app = FastAPI(
    title="KNOGMENT_NAYE - GraphRAG API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Estado del servidor."""
    return {
        "status": "ok",
        "model_loaded": rag_pipeline is not None
    }


@app.post("/api/v1/query", response_model=QueryResponse)
def responder_pregunta(payload: QueryRequest):
    """Endpoint principal de consulta GraphRAG. Devuelve respuesta + trazabilidad completa.

    Internamente, la resolución de cada sección (dentro de rag_pipeline.responder_consulta)
    puede disparar una descarga puntual a OCI la primera vez que se necesita un
    documento_id nuevo (ver IndiceGrafo._resolver_documento_lazy). Consultas
    posteriores al mismo documento no vuelven a tocar red (queda cacheado en RAM).
    """
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="El modelo GraphRAG aún no está inicializado.")

    try:
        t0 = time.time()
        # responder_consulta ahora devuelve un dict: {respuesta, trazabilidad, tiempo_segundos}
        resultado = rag_pipeline.responder_consulta(payload.pregunta)
        t1 = time.time()

        return QueryResponse(
            pregunta=payload.pregunta,
            respuesta=resultado["respuesta"],
            trazabilidad=resultado.get("trazabilidad", []),
            tiempo_segundos=round(t1 - t0, 2)
        )
    except Exception as e:
        logger.error("Error al procesar la consulta: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Error interno procesando la consulta: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=5000, reload=True)