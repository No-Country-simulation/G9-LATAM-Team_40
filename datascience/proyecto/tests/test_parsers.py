"""Pruebas para los parseadores de texto y Markdown."""
import pytest
from extraccion.extraccion import parsear_markdown_a_secciones


def test_parsear_markdown_a_secciones_basico():
    """Verifica que un texto en Markdown con encabezados se divida correctamente en secciones."""
    md_ejemplo = """# Ley de Seguridad y Salud en el Trabajo

## Artículo 1. Objeto de la Ley
La presente Ley tiene por objeto promover una cultura de prevención de riesgos laborales.

## Artículo 2. Ámbito de aplicación
Aplica a todos los sectores económicos y servicios.
"""
    secciones = parsear_markdown_a_secciones(md_ejemplo)

    assert isinstance(secciones, list)
    assert len(secciones) == 2
    assert "Artículo 1" in secciones[0]["titulo"]
    assert "prevención de riesgos" in secciones[0]["contenido"]