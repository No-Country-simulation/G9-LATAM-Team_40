"""Estructuras de datos compartidas por el pipeline de limpieza (Etapa 0)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LineaFuente:
    """Una línea de texto ya extraída de un documento, con su número de línea
    dentro de la representación de texto plano generada por el extractor
    (pdf_processor/docx_processor/txt_processor) para ESE archivo.

    Nota sobre "línea de origen": un PDF/DOCX no tiene un concepto físico de
    "línea" en el binario original, así que linea_original se refiere a la
    posición dentro del texto plano extraído (1-indexado) — es la unidad de
    trazabilidad reproducible y consistente entre re-ejecuciones del pipeline.
    """
    texto: str
    linea_original: int


@dataclass
class BloqueTexto:
    """Un bloque de texto ya reconstruido gramaticalmente: uno o varios
    LineaFuente fusionados en un párrafo, o una línea de encabezado/título."""
    texto: str
    linea_inicio: int
    linea_fin: int
    es_titulo: bool = False


@dataclass
class Seccion:
    """Una sección lógica del documento, con trazabilidad de línea."""
    titulo: str
    nivel: int
    texto: str
    linea_inicio: int
    linea_fin: int
    ruta_jerarquica: list[str] = field(default_factory=list)


@dataclass
class DocumentoLimpio:
    """Resultado final del pipeline de limpieza para un archivo fuente."""
    source_path: str
    titulo: str
    categoria: str
    tipo_documento: str
    processed_date: str
    secciones: list[Seccion] = field(default_factory=list)

    def a_markdown(self) -> str:
        frontmatter = (
            "---\n"
            f'title: "{self.titulo}"\n'
            f'source_path: "{self.source_path}"\n'
            f'category: "{self.categoria}"\n'
            f'processed_date: "{self.processed_date}"\n'
            "---\n\n"
        )
        cuerpo = []
        for sec in self.secciones:
            if sec.titulo:
                cuerpo.append(f"{'#' * max(sec.nivel, 1)} {sec.titulo}")
            if sec.texto:
                cuerpo.append(sec.texto)
        return frontmatter + "\n\n".join(cuerpo)

    def a_dict_trazabilidad(self) -> dict:
        return {
            "source_path": self.source_path,
            "titulo": self.titulo,
            "categoria": self.categoria,
            "tipo_documento": self.tipo_documento,
            "processed_date": self.processed_date,
            "secciones": [
                {
                    "titulo": s.titulo,
                    "nivel": s.nivel,
                    "texto": s.texto,
                    "linea_inicio": s.linea_inicio,
                    "linea_fin": s.linea_fin,
                    "ruta_jerarquica": s.ruta_jerarquica,
                }
                for s in self.secciones
            ],
        }
