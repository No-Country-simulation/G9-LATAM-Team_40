"""
Esquemas de Pydantic para la API de FastAPI.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    pregunta: str = Field(
        ...,
        description="Pregunta o consulta del usuario basada en ISOs y leyes.",
        example="¿Cuáles son las principales exigencias?"
    )


class TrazabilidadSeccion(BaseModel):
    seccion_id: str
    documento_id: str
    documento_nombre: str
    titulo_seccion: str
    ruta_jerarquica: List[str] = []
    nivel: int
    dominio: str
    score: float


class QueryResponse(BaseModel):
    pregunta: str
    respuesta: str
    trazabilidad: List[TrazabilidadSeccion] = []
    tiempo_segundos: float