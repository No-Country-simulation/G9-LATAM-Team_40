"""
Esquemas de Pydantic para la API de FastAPI.
"""
from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    pregunta: str = Field(
        ...,
        description="Pregunta o consulta del usuario basada en ISOs y leyes.",
        json_schema_extra={"example": "¿Cuáles son las principales exigencias?"}
    )


class TrazabilidadSeccion(BaseModel):
    """
    IMPORTANTE: estos campos deben coincidir EXACTO con las claves que arma
    PipelineGraphRAG.responder_consulta() en main.py (ver el dict dentro de
    "trazabilidad"). Si cambias un nombre de campo en uno de los dos lugares,
    cámbialo también en el otro, o FastAPI devolverá 500 (ValidationError) al
    intentar construir QueryResponse.
    """
    documento_id: str
    documento_titulo: str
    categoria: str = ""
    palabras_clave: List[str] = []
    titulo_seccion: str
    ruta_jerarquica: List[str] = []
    nivel: int
    dominio: str
    score: float
    source_path: str = ""


class QueryResponse(BaseModel):
    pregunta: str
    respuesta: str
    trazabilidad: List[TrazabilidadSeccion] = []
    tiempo_segundos: float