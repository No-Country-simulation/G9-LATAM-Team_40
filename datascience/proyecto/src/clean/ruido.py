"""Detección y eliminación de ruido típico de conversión de PDFs/DOCX a
texto: encabezados y pies repetidos, números de página, avisos de copyright,
divisores visuales, y artefactos de OCR/conversión. Opera sobre LineaFuente
para preservar el número de línea original de cada sobreviviente."""
from __future__ import annotations

import re
from collections import Counter
from typing import List, Tuple

from .modelos import LineaFuente

PATRONES_RUIDO_GENERICO = [
    re.compile(r"^\s*p[aá]gina\s+\d+\s+de\s+\d+\s*$", re.I),
    re.compile(r"^\s*page\s+\d+\s+of\s+\d+\s*$", re.I),
    re.compile(r"^\s*-\s*\d+\s*-\s*$"),
    re.compile(r"^\s*\d+\s*$"),                          # número de página suelto
    re.compile(r"https?://\S+"),
    re.compile(r"www\.\S+"),
    re.compile(r"©\s*ISO\s*\d{4}", re.I),
    re.compile(r"DOCUMENTO\s+PROTEGIDO\s+POR\s+COPYRIGHT", re.I),
    re.compile(r"TODOS\s+LOS\s+DERECHOS\s+RESERVADOS", re.I),
    re.compile(r"ALL\s+RIGHTS\s+RESERVED", re.I),
    re.compile(r"Publicado\s+en\s+Suiza", re.I),
    re.compile(r"Printed\s+in\s+Switzerland", re.I),
    re.compile(r"www\.iso\.org", re.I),
    re.compile(r"^[-_=]{3,}$"),                          # divisores visuales
    re.compile(r"^\*{3,}$"),
    re.compile(r"^[•·●▪■◆]+$"),
    re.compile(r"^[|]{2,}$"),
    re.compile(r"^[.]{5,}$"),
    re.compile(r"^\s*'''"),
    re.compile(r"^\s*```"),
]


def _texto_normalizado(linea: str) -> str:
    return linea.strip().lower()


def detectar_lineas_repetidas(
    lineas: List[LineaFuente],
    min_repeticiones: int = 3,
    patrones_preservar: List[re.Pattern] | None = None,
) -> set[str]:
    """Detecta líneas (normalizadas) que se repiten muchas veces en el
    documento — típico de encabezados/pies inyectados por el conversor en
    cada página. patrones_preservar evita marcar como ruido líneas que
    contengan referencias oficiales importantes (p.ej. dominios .cl en leyes
    chilenas) aunque se repitan."""
    patrones_preservar = patrones_preservar or []
    frecuencia = Counter()
    for l in lineas:
        norm = _texto_normalizado(l.texto)
        if not norm or len(norm) < 5:
            continue
        if any(p.search(l.texto) for p in patrones_preservar):
            continue
        frecuencia[norm] += 1
    return {norm for norm, count in frecuencia.items() if count >= min_repeticiones}


def eliminar_ruido(
    lineas: List[LineaFuente],
    lineas_repetidas: set[str] | None = None,
    patrones_extra: List[re.Pattern] | None = None,
) -> List[LineaFuente]:
    """Filtra ruido genérico + líneas repetidas detectadas, preservando el
    número de línea original de cada sobreviviente (los huecos en la
    numeración son esperados y correctos: marcan dónde se quitó ruido)."""
    lineas_repetidas = lineas_repetidas or set()
    patrones = PATRONES_RUIDO_GENERICO + (patrones_extra or [])

    resultado = []
    for l in lineas:
        limp = l.texto.strip()
        if not limp:
            continue
        if _texto_normalizado(limp) in lineas_repetidas:
            continue
        if any(p.search(limp) for p in patrones):
            continue
        resultado.append(LineaFuente(texto=limp, linea_original=l.linea_original))
    return resultado


def separar_indice_y_bibliografia(
    lineas: List[LineaFuente],
    patron_entrada_indice: re.Pattern,
) -> Tuple[List[LineaFuente], List[LineaFuente], List[LineaFuente]]:
    """Separa el cuerpo principal del índice y de la bibliografía. Ninguno de
    los dos aporta valor semántico al LLM/spaCy en Etapa 1, pero se
    conservan aparte (no se descartan) por si se necesitan para metadata."""
    patron_indice = re.compile(r"^(ÍNDICE|INDICE|CONTENIDO|TABLA\s+DE\s+CONTENIDO)\b", re.I)
    patron_biblio = re.compile(r"^(Bibliograf[ií]a|Referencias(\s+bibliogr[aá]ficas)?)\s*$", re.I)

    cuerpo, indice, biblio = [], [], []
    modo = "cuerpo"

    for l in lineas:
        limp = l.texto.strip()
        if patron_indice.match(limp):
            modo = "indice"
            indice.append(l)
            continue
        if patron_biblio.match(limp):
            modo = "biblio"
            biblio.append(l)
            continue

        if modo == "indice":
            if patron_entrada_indice.match(limp) or ("...." in limp) or ("----" in limp):
                indice.append(l)
                continue
            modo = "cuerpo"  # un encabezado real termina la zona de índice
        if modo == "biblio":
            biblio.append(l)
            continue

        cuerpo.append(l)

    return cuerpo, indice, biblio
