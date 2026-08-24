"""Esquemas públicos e internos de la API GraphRAG."""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


Corpus = Literal["BASE", "PRIVADO"]
Dominio = Literal["ISOS", "LEYES"]


class QueryRequest(BaseModel):
    pregunta: str = Field(
        ...,
        min_length=20,
        description="Pregunta o consulta del usuario basada en ISOs y leyes.",
        json_schema_extra={"example": "¿Cuáles son las principales exigencias?"},
    )
    user_id: UUID


class TrazabilidadSeccion(BaseModel):
    """Wire exacto producido por PipelineGraphRAG y validado por FastAPI."""

    documento_id: str
    documento_titulo: str
    categoria: str = ""
    palabras_clave: list[str] = Field(default_factory=list)
    titulo_seccion: str
    ruta_jerarquica: list[str] = Field(default_factory=list)
    nivel: int
    dominio: str
    score: float
    corpus: Corpus
    archivo_id: UUID | None = None


class QueryResponse(BaseModel):
    pregunta: str
    respuesta: str
    trazabilidad: list[TrazabilidadSeccion] = Field(default_factory=list)
    tiempo_segundos: float


class IndexDocumentRequest(BaseModel):
    archivo_id: UUID
    documento_id: str
    nombre_original: str
    dominio: Dominio
    object_name: str


class IndexJobRequest(BaseModel):
    user_id: UUID
    generation: int
    idempotency_key: str
    purge_previous_releases: bool = False
    documentos: list[IndexDocumentRequest] = Field(default_factory=list)


class IndexJobResponse(BaseModel):
    job_id: UUID
    status: Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "SUPERSEDED"]
    stage: Literal["DOWNLOAD", "CLEAN", "EXTRACT", "CLASSIFY", "GRAPH", "PUBLISH", "RELOAD", "PURGE"] | None = None
    message: str | None = None
    release_id: str | None = None
    generation: int
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class IndexGraphResponse(BaseModel):
    user_id: UUID
    release_id: str | None = None
    generation: int | None = None
    created_at: datetime | None = None
    json_data: dict = Field(default_factory=dict)
