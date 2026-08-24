"""FastAPI interna para consultas GraphRAG y releases privados."""
from __future__ import annotations

import logging
import secrets
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from settings import settings
from indexacion.jobs import TenantIndexJobManager
from indexacion.main import PipelineGraphRAG
from indexacion.tenant_registry import TenantIndexRegistry
from .schemas import IndexGraphResponse, IndexJobRequest, IndexJobResponse, QueryRequest, QueryResponse

logger = logging.getLogger("API")
rag_pipeline: PipelineGraphRAG | None = None
registry: TenantIndexRegistry | None = None
job_manager: TenantIndexJobManager | None = None


def require_internal_token(
    token: str | None = Header(default=None, alias="X-ML-Internal-Token"),
) -> None:
    if not settings.ML_INTERNAL_TOKEN.strip() or token is None or not secrets.compare_digest(token, settings.ML_INTERNAL_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token interno inválido")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_pipeline, registry, job_manager
    settings.ensure_dirs()
    settings.validate_internal_token()
    registry = TenantIndexRegistry(settings)
    job_manager = TenantIndexJobManager(settings, registry)
    logger.info("Cargando Pipeline GraphRAG base...")
    rag_pipeline = PipelineGraphRAG(settings, registry)
    app.state.registry = registry
    app.state.job_manager = job_manager
    yield
    if job_manager is not None:
        job_manager.close()
    logger.info("Servidor apagado.")


app = FastAPI(
    title="KNOGMENT_NAYE - GraphRAG API",
    version="1.0.0",
    lifespan=lifespan,
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
    return {"status": "ok", "model_loaded": rag_pipeline is not None}


@app.post("/api/v1/query", response_model=QueryResponse)
def responder_pregunta(payload: QueryRequest, _: None = Depends(require_internal_token)):
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="El modelo GraphRAG aún no está inicializado.")
    try:
        started = perf_counter()
        resultado = rag_pipeline.responder_consulta(payload.pregunta, payload.user_id)
        elapsed = resultado.get("tiempo_segundos")
        if elapsed is None:
            elapsed = round(perf_counter() - started, 2)
        return QueryResponse(
            pregunta=payload.pregunta,
            respuesta=resultado["respuesta"],
            trazabilidad=resultado.get("trazabilidad", []),
            tiempo_segundos=elapsed,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error al procesar la consulta")
        raise HTTPException(status_code=500, detail=f"Error interno procesando la consulta: {exc}") from exc


@app.post("/api/v1/index-jobs", response_model=IndexJobResponse, status_code=status.HTTP_202_ACCEPTED)
def crear_job(payload: IndexJobRequest, _: None = Depends(require_internal_token)):
    if job_manager is None:
        raise HTTPException(status_code=503, detail="El gestor de indexación aún no está inicializado.")
    try:
        return job_manager.create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/index-jobs/{job_id}", response_model=IndexJobResponse)
def consultar_job(job_id: UUID, _: None = Depends(require_internal_token)):
    if job_manager is None:
        raise HTTPException(status_code=503, detail="El gestor de indexación aún no está inicializado.")
    result = job_manager.get(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return result


@app.get("/api/v1/indexes/{user_id}/graph", response_model=IndexGraphResponse)
def consultar_grafo_privado(user_id: UUID, _: None = Depends(require_internal_token)):
    if registry is None:
        raise HTTPException(status_code=503, detail="El registro de índices aún no está inicializado.")
    data = registry.graph(user_id)
    return IndexGraphResponse(user_id=user_id, **data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=5000)
