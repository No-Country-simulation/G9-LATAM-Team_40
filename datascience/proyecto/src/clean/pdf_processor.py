from __future__ import annotations

import logging
import re  # <--- IMPORTANTE: Importamos re para limpiar HTML
from collections import Counter
from pathlib import Path

import fitz
import ftfy
import pymupdf4llm

from .modelos import LineaFuente

logger = logging.getLogger("clean.pdf_processor")

try:
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_DISPONIBLE = True
except ImportError:
    UNSTRUCTURED_DISPONIBLE = False
    logger.warning("No se encontró 'unstructured'. Usando pymupdf4llm como respaldo.")

TIPOS_RUIDO_UNSTRUCTURED = {"Header", "Footer", "PageBreak"}

def _detectar_headers_footers_repetidos(doc: fitz.Document, min_paginas: int = 3) -> tuple[list[str], list[str]]:
    if len(doc) < min_paginas:
        return [], []

    indices = sorted(set(list(range(min(5, len(doc)))) + list(range(max(0, len(doc) - 5), len(doc)))))
    headers, footers = [], []

    for idx in indices:
        blocks = sorted(doc[idx].get_text("blocks"), key=lambda b: b[1])
        if not blocks:
            continue
            
        if blocks[0][6] == 0 and 0 < len(blocks[0][4].strip()) < 150:
            headers.append(blocks[0][4].strip())
        if len(blocks) > 1 and blocks[-1][6] == 0 and 0 < len(blocks[-1][4].strip()) < 150:
            footers.append(blocks[-1][4].strip())

    headers_comunes = [t for t, c in Counter([h.lower() for h in headers]).items() if c >= min_paginas]
    footers_comunes = [t for t, c in Counter([f.lower() for f in footers]).items() if c >= min_paginas]
    
    return headers_comunes, footers_comunes

def _extraer_con_unstructured(ruta_pdf: Path) -> list[LineaFuente]:
    elementos = partition_pdf(filename=str(ruta_pdf), strategy="hi_res", infer_table_structure=True)
    lineas: list[LineaFuente] = []
    
    for i, el in enumerate(elementos, start=1):
        if type(el).__name__ in TIPOS_RUIDO_UNSTRUCTURED:
            continue
        texto = str(el).strip()
        
        # <--- LIMPIEZA HTML AQUÍ --->
        texto = re.sub(r'<[^>]+>', '', texto).strip()
        
        if texto:
            lineas.append(LineaFuente(texto=texto, linea_original=i))
            
    return lineas

def _extraer_con_pymupdf(ruta_pdf: Path) -> list[LineaFuente]:
    doc = fitz.open(str(ruta_pdf))
    headers_c, footers_c = _detectar_headers_footers_repetidos(doc)
    doc.close()

    paginas_md = pymupdf4llm.to_markdown(str(ruta_pdf), page_chunks=True)
    texto_crudo = "\n\n".join(p.get("text", "").strip() for p in paginas_md if p.get("text"))
    texto_crudo = ftfy.fix_text(texto_crudo)

    lineas: list[LineaFuente] = []
    for i, l in enumerate(texto_crudo.split("\n"), start=1):
        limp = l.strip()
        
        # <--- LIMPIEZA HTML AQUÍ --->
        limp = re.sub(r'<[^>]+>', '', limp).strip()
        
        if not limp:
            continue
            
        texto_comparacion = limp.lower().strip("*#_ ")
        if texto_comparacion in headers_c or texto_comparacion in footers_c:
            continue
            
        lineas.append(LineaFuente(texto=limp, linea_original=i))
        
    return lineas



def extraer_lineas_pdf(ruta_pdf: Path, forzar_fallback: bool = False) -> list[LineaFuente]:
    if UNSTRUCTURED_DISPONIBLE and not forzar_fallback:
        try:
            return _extraer_con_unstructured(ruta_pdf)
        except Exception as e:
            logger.warning("Error en unstructured: %s. Usando fallback pymupdf4llm.", e)
            
    return _extraer_con_pymupdf(ruta_pdf)