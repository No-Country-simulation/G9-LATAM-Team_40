"""Extracción de entidades de dominio (regex/diccionario) y parseo de Markdown a secciones."""
from __future__ import annotations

import re
from pathlib import Path

from .normalizacion import normalizar_key, normalizar_texto

REGEX_HEADER = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")
REGEX_INDICE = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?\s*(Índice|Contenido|Table of contents)(?:\s+Página)?\s*(?:\*\*)?", re.I)

REGEX_BIBLIOGRAFIA = re.compile(
    r"^\s*(?:#{1,6}\s*)?\**\s*(Bibliografía|Bibliografia|Referencias bibliográficas|Referencias)\s*\**\s*$",
    re.IGNORECASE
)

# Patrón para validar que una línea en la bibliografía cumpla con estructuras típicas de referencias
REGEX_PATRON_REFERENCIA = re.compile(
    r"(?:\(\d{4}\)|\[\d+\]|\b(?:Ed\.|Vol\.|pp\.|doi:|ISBN|ISO|IEC)\b|\b(?:19|20)\d{2}\b)",
    re.I
)

REGEX_MEDICION = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:%|°C|°F|mm|cm|m|km|mg|g|kg|ml|l|Pa|kPa|MPa|bar|V|kV|A|mA|W|kW|Hz|kHz|MHz|GHz|dB|dBA|lux|lx|ppm|h|min|s)\b",
    re.I,
)

PATRONES_RUIDO = [
    # URLs
    re.compile(r"https?://\S+", re.I),
    re.compile(r"www\.\S+", re.I),
    # Números de página
    re.compile(r"^\s*página\s+\d+\s+de\s+\d+\s*$", re.I),
    re.compile(r"^\s*page\s+\d+\s+of\s+\d+\s*$", re.I),
    re.compile(r"^\s*-\s*\d+\s*-\s*$"),
    re.compile(r"^\s*\d+\s*$"),
    # Copyright
    re.compile(r"©\s*ISO\s*\d{4}", re.I),
    re.compile(r"DOCUMENTO\s+PROTEGIDO\s+POR\s+COPYRIGHT", re.I),
    re.compile(r"TODOS\s+LOS\s+DERECHOS\s+RESERVADOS", re.I),
    re.compile(r"ALL\s+RIGHTS\s+RESERVED", re.I),
    # Publicación
    re.compile(r"Publicado\s+en\s+Suiza", re.I),
    re.compile(r"Printed\s+in\s+Switzerland", re.I),
    # Sitios web editoriales
    re.compile(r"www\.iso\.org", re.I),
    re.compile(r"www\.iso\.org/obp", re.I),
    # Líneas decorativas
    re.compile(r"^[-_=]{3,}$"),
    re.compile(r"^\*{3,}$"),
    # Encabezados markdown vacíos
    re.compile(r"^\s*#{1,6}\s*$"),
    # Separadores
    re.compile(r"^[•·●▪■◆]+$"),
    re.compile(r"^[\-=*_]{5,}$"),
    # Saltos OCR
    re.compile(r"^[|]{2,}$"),
    re.compile(r"^[.]{5,}$"),
    re.compile(r"iso\.org", re.I),
    re.compile(r"^\s*\d+\s+Traducción oficial/Official translation/Traduction officielle.*©\s*ISO\s*\d{4}.*$", re.I),
    re.compile(r"Traducción oficial/Official translation/Traduction officielle\s+©\s*ISO\s*\d{4}", re.I),
    re.compile(r"^\s*>?\s*\d+\s+Disponible en:.*©\s*ISO\s*\d{4}.*$", re.I),
    re.compile(r"^\s*\d+\s+(?=Traducción oficial)", re.I),
    re.compile(r"^\s*Este documento consiste.*", re.I),
    re.compile(r"^\s*Sólo debe considerarse como una consulta.*", re.I),
    re.compile(r"^\s*El único documento oficial es.*", re.I),
    re.compile(r"ISO\s+\d+\s*:\s*\d{4}\s*-\s*Traducción.*$", re.I),
]


def construir_patrones_dominio(diccionario_dominio: dict[str, list[str]]) -> list[tuple[str, re.Pattern]]:
    patrones = []
    for categoria, terminos in diccionario_dominio.items():
        if not terminos:
            continue
        terminos_ordenados = sorted(terminos, key=len, reverse=True)
        patron = re.compile(r"\b(" + "|".join(re.escape(t) for t in terminos_ordenados) + r")\b", re.I)
        patrones.append((categoria, patron))
    return patrones


def extraer_entidades_dominio(
    texto: str,
    indice_entidades: dict[str, dict[str, str]],
    patrones_dominio: list[tuple[str, re.Pattern]],
) -> list[dict]:
    entidades = []

    for categoria, patron in patrones_dominio:
        for match in patron.finditer(texto):
            valor = match.group(0)
            info = indice_entidades.get(normalizar_key(valor), {})
            entidades.append({
                "texto": valor,
                "texto_normalizado": normalizar_texto(valor),
                "canonical": info.get("canonical", valor.upper()),
                "tipo": info.get("tipo", categoria),
                "origen": "diccionario_dominio",
                "inicio": match.start(),
                "fin": match.end(),
                "contexto": texto[max(0, match.start() - 100):min(len(texto), match.end() + 150)],
            })

    for match in REGEX_MEDICION.finditer(texto):
        valor = match.group(0)
        entidades.append({
            "texto": valor,
            "texto_normalizado": normalizar_texto(valor),
            "canonical": valor.upper(),
            "tipo": "PARAMETRO_TECNICO",
            "origen": "regex",
            "inicio": match.start(),
            "fin": match.end(),
            "contexto": texto[max(0, match.start() - 100):min(len(texto), match.end() + 150)],
        })

    return entidades


def limpiar_texto_raw(texto: str) -> str:
    resultado = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        if any(p.search(linea) for p in PATRONES_RUIDO):
            continue
        resultado.append(linea)
    return "\n".join(resultado)


def extraer_indice(lineas: list[str]) -> list[str]:
    indice = []
    dentro_indice = False

    for linea in lineas:
        linea_str = linea.strip()

        if REGEX_INDICE.match(linea_str):
            dentro_indice = True
            continue

        if dentro_indice:
            # Si encuentra la bibliografía o un encabezado markdown real que no sea otro índice, se detiene
            if REGEX_BIBLIOGRAFIA.match(linea_str):
                break
            if REGEX_HEADER.match(linea_str) and not REGEX_INDICE.match(linea_str):
                break

            if not linea_str:
                continue

            # Filtrar ruido típico de normas ISO en el índice
            if any(palabra in linea_str for palabra in ["Traducción oficial", "ISO 2015", "derechos reservados", "©"]):
                continue

            if linea_str.isdigit():
                continue

            limpio = re.sub(r"[|*_#]", "", linea_str).strip()
            if limpio:
                # Si el índice viene comprimido en una sola línea con puntos o guiones largos
                if "...." in limpio or "----" in limpio:
                    fragmentos = re.split(r"(?:\.{3,}|[-—]{2,})", limpio)
                    for frag in fragmentos:
                        f_limpio = frag.strip()
                        if len(f_limpio) > 2:
                            indice.append(f_limpio)
                else:
                    limpio_formateado = re.sub(r"\s{2,}", " ", limpio)
                    indice.append(limpio_formateado)

    return indice


def extraer_bibliografia(lineas: list[str]) -> list[str]:
    bibliografia = []
    dentro_bibliografia = False

    for linea in lineas:
        linea_str = linea.strip()

        if REGEX_BIBLIOGRAFIA.match(linea_str):
            dentro_bibliografia = True
            continue

        if dentro_bibliografia:
            if REGEX_HEADER.match(linea_str):
                break

            limpio = re.sub(r"[|*_#]", "", linea_str).strip()
            
            if limpio:
                # Descartar números de página sueltos o texto demasiado corto
                if limpio.isdigit() or len(limpio) < 5:
                    continue

                if any(palabra in limpio for palabra in ["Traducción oficial", "ISO", "derechos reservados", "©"]):
                    continue

                if REGEX_PATRON_REFERENCIA.search(limpio) or len(bibliografia) >= 0:
                    bibliografia.append(limpio)

    return bibliografia


def parsear_markdown_a_secciones(filepath: Path) -> dict:
    lineas = filepath.read_text(encoding="utf-8").splitlines()
    indice = extraer_indice(lineas)
    bibliografia = extraer_bibliografia(lineas)
    
    secciones: list[dict] = []
    stack: list[tuple[int, str]] = []
    buffer: list[str] = []

    def guardar():
        if buffer and stack:
            texto = limpiar_texto_raw("\n".join(buffer))
            if texto:
                secciones.append({
                    "titulo": stack[-1][1],
                    "nivel": stack[-1][0],
                    "ruta_jerarquica": [x[1] for x in stack],
                    "texto": texto,
                })
        buffer.clear()

    omitir_seccion = False

    for linea in lineas:
        linea_str = linea.strip()
        
        # Excluir índice y bibliografía del cuerpo principal que va al LLM/spaCy
        if REGEX_INDICE.match(linea_str) or REGEX_BIBLIOGRAFIA.match(linea_str):
            guardar()
            stack.clear()
            omitir_seccion = True
            continue

        match = REGEX_HEADER.match(linea_str)
        if match and not omitir_seccion:
            guardar()
            nivel = len(match.group(1))
            titulo = match.group(2).strip()
            while stack and stack[-1][0] >= nivel:
                stack.pop()
            stack.append((nivel, titulo))
        else:
            if not omitir_seccion:
                buffer.append(linea)

    guardar()
    return {
        "metadata": {
            "indice": indice,
            "bibliografia": bibliografia
        },
        "secciones": secciones
    }