"""Pruebas de los contratos Pydantic públicos e internos."""
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.api.schemas import IndexJobRequest, QueryRequest, QueryResponse, TrazabilidadSeccion


def test_query_request_requiere_usuario_y_pregunta():
    user_id = uuid4()
    request = QueryRequest(
        pregunta="¿Cuáles son las obligaciones del empleador?",
        user_id=user_id,
    )
    assert request.user_id == user_id


def test_query_request_invalido_sin_usuario():
    with pytest.raises(ValidationError):
        QueryRequest(pregunta="¿Cuáles son las obligaciones del empleador?")


def test_query_response_conserva_score_y_scope():
    trace = TrazabilidadSeccion(
        documento_id="doc",
        documento_titulo="Manual",
        titulo_seccion="Seguridad",
        nivel=1,
        dominio="ISOs",
        score=0.8,
        corpus="BASE",
    )
    response = QueryResponse(
        pregunta="¿Qué es la ISO 45001?",
        respuesta="Es una norma de SST.",
        trazabilidad=[trace],
        tiempo_segundos=1.45,
    )
    assert response.trazabilidad[0].score == 0.8
    assert response.trazabilidad[0].corpus == "BASE"


def test_index_job_key_and_empty_documents():
    user_id = uuid4()
    request = IndexJobRequest(
        user_id=user_id,
        generation=3,
        idempotency_key=f"{user_id}:3",
        documentos=[],
    )
    assert request.documentos == []
