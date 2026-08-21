"""Pruebas para los parseadores de texto y Markdown."""
from pathlib import Path

from extraccion.extraccion import parsear_markdown_a_secciones


def test_parsear_markdown_a_secciones_basico(tmp_path: Path):
    """Verifica que un Markdown se divida en secciones con metadata."""
    md_ejemplo = """# Ley de Seguridad y Salud en el Trabajo

## Artículo 1. Objeto de la Ley
La presente Ley tiene por objeto promover una cultura de prevención de riesgos laborales.

## Artículo 2. Ámbito de aplicación
Aplica a todos los sectores económicos y servicios.
"""
    ruta = tmp_path / "ejemplo.md"
    ruta.write_text(md_ejemplo, encoding="utf-8")

    resultado = parsear_markdown_a_secciones(ruta)
    secciones = resultado["secciones"]

    assert isinstance(resultado, dict)
    assert len(secciones) == 2
    assert "Artículo 1" in secciones[0]["titulo"]
    assert "prevención de riesgos" in secciones[0]["texto"]