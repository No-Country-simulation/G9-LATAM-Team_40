"""Extracción de texto desde TXT plano. Sin ruido de conversión de PDF/DOCX,
pero sí normaliza codificación."""
from __future__ import annotations

from pathlib import Path
from typing import List

import ftfy

from .modelos import LineaFuente


def extraer_lineas_txt(ruta_txt: Path) -> List[LineaFuente]:
    texto = ruta_txt.read_text(encoding="utf-8", errors="ignore")
    texto = ftfy.fix_text(texto)

    lineas = []
    for i, l in enumerate(texto.split("\n"), start=1):
        limp = l.strip()
        if limp:
            lineas.append(LineaFuente(texto=limp, linea_original=i))
    return lineas
