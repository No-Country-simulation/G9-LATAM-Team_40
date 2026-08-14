"""Normalización de texto e índices de entidades de dominio."""
from __future__ import annotations

import re

from unidecode import unidecode

def normalizar_texto(texto: str) -> str:
    texto = unidecode(str(texto)).lower()
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def normalizar_key(texto: str) -> str:
    return normalizar_texto(texto).replace(" ", "").upper()


def construir_indice_entidades(diccionario: dict[str, list[str]]) -> dict[str, dict[str, str]]:
    """Mapea cada término (normalizado) a su forma canónica y su tipo/categoría."""
    indice: dict[str, dict[str, str]] = {}
    for categoria, terminos in diccionario.items():
        if not terminos:
            continue
        canonical = terminos[0].upper()
        for termino in terminos:
            indice[normalizar_key(termino)] = {"canonical": canonical, "tipo": categoria}
    return indice
