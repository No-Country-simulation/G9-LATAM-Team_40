"""Pruebas para la validación de esquemas Pydantic."""
import pytest
from pydantic import ValidationError
from src.api.schemas import QueryRequest, QueryResponse


def test_query_request_valido():
    """Prueba la instanciación correcta de un payload de consulta."""
    request = QueryRequest(pregunta="¿Cuáles son las obligaciones del empleador?")
    assert request.pregunta == "¿Cuáles son las obligaciones del empleador?"


def test_query_request_invalido_sin_pregunta():
    """Verifica que Pydantic lance un error si falta el campo obligatorio 'pregunta'."""
    with pytest.raises(ValidationError):
        QueryRequest()


def test_query_response_valido():
    """Prueba la estructura de respuesta final."""
    response = QueryResponse(
        pregunta="¿Qué es la ISO 45001?",
        respuesta="Es la norma internacional para sistemas de gestión de SST.",
        tiempo_segundos=1.45
    )
    assert response.tiempo_segundos > 0