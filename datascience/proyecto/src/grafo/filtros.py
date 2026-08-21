"""
Módulo de filtros y normalización de texto para el sistema KNOGMENT_NAYE.
"""
from __future__ import annotations

import re
from unidecode import unidecode

ARTICULOS_Y_PRONOMBRES = re.compile(
    r"^(el|la|los|las|un|una|unos|unas|mi|mis|tu|tus|su|sus|nuestro|nuestra|nuestros|nuestras)\s+",
    re.IGNORECASE
)

FRASES_VERBALES_NO_ENTIDAD = re.compile(
    r"\b(consiste|incluye|contiene|tiene|hace|gestiona|identifica|certifica|"
    r"debe|puede|sirve|aplica|corresponde|permite|busca|asegura|garantiza)\b",
    re.IGNORECASE
)

SIGLAS_CONOCIDAS = {
    "iso": "ISO",
    "chile": "Chile",
    "sucursal": "Sucursal",
}

# Términos genéricos, conectores y palabras basura que rompen el grafo
TERMINOS_GENERICOS = {
    "algo", "esto", "eso", "aquello", "cosa", "cosas",
    "manera", "forma", "tipo", "clase", "aspecto",
    "que", "el que", "los que", "la que", "las que",
    "de que", "en que", "a que", "por que", "para que", "con que", "del que",
    "como", "cuando", "donde", "quien", "quienes", "cual", "cuales",
    "y", "o", "u", "e", "pero", "sino", "mas", "although", "aunque"
}

def limpiar_puntuacion(texto: str) -> str:
    t = texto.strip(" .,;:!?()[]{}\"'")
    t = re.sub(r"\s+", " ", t)
    return t

def corregir_siglas(texto: str) -> str:
    palabras = texto.split()
    corregidas = []
    for p in palabras:
        clave = p.lower()
        corregidas.append(SIGLAS_CONOCIDAS.get(clave, p))
    return " ".join(corregidas)

def es_entidad_valida(texto: str) -> bool:
    t = texto.lower().strip()
    return t not in TERMINOS_GENERICOS and len(t) >= 3

def limpiar_label(texto: str) -> str:
    t = (texto or "").strip()
    if not t or not es_entidad_valida(t):
        return "" 
    
    t = limpiar_puntuacion(t)
    t = ARTICULOS_Y_PRONOMBRES.sub("", t).strip()
    if not t:
        t = texto.strip()
    
    t = t.title()
    t = corregir_siglas(t)
    
    if FRASES_VERBALES_NO_ENTIDAD.search(t):
        palabras = t.split()
        for i, p in enumerate(palabras):
            if FRASES_VERBALES_NO_ENTIDAD.match(p):
                t = " ".join(palabras[:i]) or t
                break
                
    t = limpiar_puntuacion(t)
    return t if es_entidad_valida(t) else ""

def es_texto_valido(texto: str) -> bool:
    t = (texto or "").strip()
    if len(t) < 3:
        return False
    if t[0] in ":-.,;()":
        return False
    if re.match(r"^\d+\s*\w{0,2}$", t):
        return False
    if t.lower() in TERMINOS_GENERICOS:
        return False
    return True

def normalizar_texto(texto: str) -> str:
    texto = unidecode(str(texto))
    texto = texto.lower()
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()

def normalizar_key(texto: str) -> str:
    return normalizar_texto(texto).replace(" ", "").upper()