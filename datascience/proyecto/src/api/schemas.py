"""Modelos Pydantic esenciales para la API REST."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    pregunta: str = Field(
        ..., 
        example="¿Cuáles son las obligaciones del empleador según la Ley SST?",
        description="Pregunta realizada por el usuario."
    )
    top_k: Optional[int] = Field(
        default=None, 
        description="Número opcional de nodos a consultar en el grafo."
    )


class QueryResponse(BaseModel):
    pregunta: str
    respuesta: str
    tiempo_segundos: float