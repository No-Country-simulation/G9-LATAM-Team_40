"""Extracción de contenido tabular desde Excel — se conserva como tabla
Markdown por hoja (funcionalidad heredada del pipeline original)."""
from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from .modelos import LineaFuente


def extraer_lineas_excel(ruta_excel: Path) -> List[LineaFuente]:
    hojas = pd.read_excel(ruta_excel, sheet_name=None)
    lineas = []
    contador = 1
    for nombre, df in hojas.items():
        lineas.append(LineaFuente(texto=f"## Hoja: {nombre}", linea_original=contador))
        contador += 1
        for l in df.to_markdown(index=False).split("\n"):
            if l.strip():
                lineas.append(LineaFuente(texto=l, linea_original=contador))
                contador += 1
    return lineas
