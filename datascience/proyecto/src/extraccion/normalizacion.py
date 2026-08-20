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


def construir_mapa_lemas(doc) -> dict[str, str]:
    """Construye un mapa {token_normalizado: lema_normalizado} a partir de un Doc de spaCy.

    Se usa para colapsar variantes flexionadas de una misma entidad de una sola
    palabra (p.ej. 'trabajador' / 'trabajadores') bajo la misma clave, evitando
    que el grafo de Etapa 3 las trate como nodos distintos.
    """
    mapa: dict[str, str] = {}
    for token in doc:
        if token.is_space or token.is_punct:
            continue
        mapa[normalizar_texto(token.text)] = normalizar_texto(token.lemma_)
    return mapa


def normalizar_key_lemma(texto: str, mapa_lemas: dict[str, str] | None = None) -> str:
    """Como normalizar_key, pero si se provee un mapa de lemas y el texto es una
    sola palabra, usa el lema en vez de la forma flexionada. Para spans de más
    de una palabra se usa el comportamiento normal (más seguro: evita romper
    frases completas por errores de lematización)."""
    texto_norm = normalizar_texto(texto)
    if mapa_lemas and " " not in texto_norm.strip():
        lema = mapa_lemas.get(texto_norm)
        if lema:
            return normalizar_key(lema)
    return normalizar_key(texto)


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