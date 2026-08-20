"""Extracción/generación de metadata YAML frontmatter para los documentos
procesados. Se conserva SOLO lo esencial: source_path (ruta absoluta, para
trazabilidad), título, categoría y fecha de procesamiento — nada de
bibliografía completa ni bloques de índice, que no aportan valor semántico y
solo inflan el contexto que después consume el LLM."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class MetadataDocumento:
    source_path: str
    titulo: str
    categoria: str
    processed_date: str

    @classmethod
    def desde_archivo(cls, ruta: Path, categoria: str) -> "MetadataDocumento":
        return cls(
            source_path=str(ruta.resolve()),
            titulo=ruta.stem,
            categoria=categoria,
            processed_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
