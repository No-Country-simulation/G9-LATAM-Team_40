

import re
from unidecode import unidecode


import re

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
    # añade más según tu dominio
}

TERMINOS_GENERICOS = {
    "algo", "esto", "eso", "aquello", "cosa", "cosas",
    "manera", "forma", "tipo", "clase", "aspecto",
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
    """Limpia el label para que sea legible en pantalla, manteniendo coherencia semántica."""
    t = (texto or "").strip()
    if not t or not es_entidad_valida(t):
        return ""  # señal para descartar el nodo
    
    # 1. Eliminar puntuación residual
    t = limpiar_puntuacion(t)
    
    # 2. Eliminar artículos/pronombres iniciales
    t = ARTICULOS_Y_PRONOMBRES.sub("", t).strip()
    if not t:
        t = texto.strip()
    
    # 3. Capitalizar tipo título
    t = t.title()
    
    # 4. Corregir siglas conocidas
    t = corregir_siglas(t)
    
    # 5. Si parece una frase verbal incompleta, acortar al primer sustantivo
    if FRASES_VERBALES_NO_ENTIDAD.search(t):
        palabras = t.split()
        for i, p in enumerate(palabras):
            if FRASES_VERBALES_NO_ENTIDAD.match(p):
                t = " ".join(palabras[:i]) or t
                break
    
    # 6. Limpieza final
    t = limpiar_puntuacion(t)
    
    return t if es_entidad_valida(t) else ""

def es_texto_valido(texto: str) -> bool:
    """Filtra ruido de parsing: fragmentos numéricos sueltos ('1 a', '2 a'),
    objetos que quedan con puntuación de lista al inicio (': -Riesgo',
    '-Accidentabilidad'), o textos demasiado cortos para ser una entidad real."""
    t = (texto or "").strip()
    if len(t) < 3:
        return False
    if t[0] in ":-.,;()":
        return False
    if re.match(r"^\d+\s*\w{0,2}$", t):
        return False
    return True


def normalizar_texto(texto: str) -> str:
    texto = unidecode(str(texto))
    texto = texto.lower()
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def normalizar_key(texto: str) -> str:
    return normalizar_texto(texto).replace(" ", "").upper()
