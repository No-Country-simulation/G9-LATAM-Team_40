"""Extracción de entidades de dominio (regex/diccionario) y parseo de Markdown a secciones."""
from __future__ import annotations

import re
from pathlib import Path

# Nuevas librerías complementarias
import spacy
from unstructured.partition.text import partition_text

from .normalizacion import normalizar_key, normalizar_texto

# ---------------------------------------------------------
# 1. CONFIGURACIÓN NLP (spaCy)
# Utilizando el modelo Transformer que tienes configurado 
# en tu entorno de variables (es_dep_news_trf)
# ---------------------------------------------------------
try:
    nlp = spacy.load("es_dep_news_trf") 
except OSError:
    import spacy.cli
    spacy.cli.download("es_dep_news_trf")
    nlp = spacy.load("es_dep_news_trf")

# ---------------------------------------------------------
# 2. VARIABLES Y REGEX ORIGINALES INTACTAS
# ---------------------------------------------------------
REGEX_INDICE = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?\s*(Índice|Contenido|Table of contents)(?:\s+Página)?\s*(?:\*\*)?", re.I)
REGEX_BIBLIOGRAFIA = re.compile(r"^\s*(?:#{1,6}\s*)?\**\s*(Bibliografía|Bibliografia|Referencias bibliográficas|Referencias)\s*\**\s*$", re.IGNORECASE)
REGEX_PATRON_REFERENCIA = re.compile(r"(?:\(\d{4}\)|\[\d+\]|\b(?:Ed\.|Vol\.|pp\.|doi:|ISBN|ISO|IEC)\b|\b(?:19|20)\d{2}\b)", re.I)
REGEX_MEDICION = re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:%|°C|°F|mm|cm|m|km|mg|g|kg|ml|l|Pa|kPa|MPa|bar|V|kV|A|mA|W|kW|Hz|kHz|MHz|GHz|dB|dBA|lux|lx|ppm|h|min|s)\b", re.I)

REGEX_HEADER_MD = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")
REGEX_HEADER_LEGAL = re.compile(r"^\s*(?:\*\*)?\s*(\d+(?:\.\d+)*)\.?\s+([A-ZÁÉÍÓÚÑ].+?)\s*(?:\*\*)?\s*$")
REGEX_HEADER_CAPITULO = re.compile(r"^\s*(?:\*\*)?\s*(CAP[IÍ]TULO|T[IÍ]TULO|ART[IÍ]CULO|SECCI[OÓ]N)\s+([IVXLCDM]+|\d+)(?:[:.-])?\s*(.*)\s*(?:\*\*)?\s*$", re.I)

PATRONES_RUIDO = [
    re.compile(r"https?://\S+", re.I),
    re.compile(r"www\.\S+", re.I),
    re.compile(r"^\s*página\s+\d+\s+de\s+\d+\s*$", re.I),
    re.compile(r"^\s*page\s+\d+\s+of\s+\d+\s*$", re.I),
    re.compile(r"^\s*-\s*\d+\s*-\s*$"),
    re.compile(r"^\s*\d+\s*$"),
    re.compile(r"©\s*ISO\s*\d{4}", re.I),
    re.compile(r"DOCUMENTO\s+PROTEGIDO\s+POR\s+COPYRIGHT", re.I),
    re.compile(r"TODOS\s+LOS\s+DERECHOS\s+RESERVADOS", re.I),
    re.compile(r"ALL\s+RIGHTS\s+RESERVED", re.I),
    re.compile(r"Publicado\s+en\s+Suiza", re.I),
    re.compile(r"Printed\s+in\s+Switzerland", re.I),
    re.compile(r"www\.iso\.org", re.I),
    re.compile(r"www\.iso\.org/obp", re.I),
    re.compile(r"^[-_=]{3,}$"),
    re.compile(r"^\*{3,}$"),
    re.compile(r"^\s*#{1,6}\s*$"),
    re.compile(r"^[•·●▪■◆]+$"),
    re.compile(r"^[\-=*_]{5,}$"),
    re.compile(r"^[|]{2,}$"),
    re.compile(r"^[.]{5,}$"),
    re.compile(r"iso\.org", re.I),
    re.compile(r"^\s*\d+\s+Traducción oficial.*©\s*ISO\s*\d{4}.*$", re.I),
    re.compile(r"Traducción oficial.*©\s*ISO\s*\d{4}", re.I),
    re.compile(r"^\s*>?\s*\d+\s+Disponible en:.*©\s*ISO\s*\d{4}.*$", re.I),
    re.compile(r"^\s*\d+\s+(?=Traducción oficial)", re.I),
    re.compile(r"^\s*Este documento consiste.*", re.I),
    re.compile(r"^\s*Sólo debe considerarse como una consulta.*", re.I),
    re.compile(r"^\s*El único documento oficial es.*", re.I),
    re.compile(r"ISO\s+\d+\s*:\s*\d{4}\s*-\s*Traducción.*$", re.I),
]


def detectar_encabezado(linea: str) -> tuple[int, str] | None:
    match_md = REGEX_HEADER_MD.match(linea)
    if match_md:
        return len(match_md.group(1)), match_md.group(2).strip()
    
    match_legal = REGEX_HEADER_LEGAL.match(linea)
    if match_legal:
        numeracion = match_legal.group(1)
        titulo_texto = match_legal.group(2).strip()
        nivel = len(numeracion.split('.'))
        if nivel <= 6:
            return nivel, f"{numeracion}. {titulo_texto}"

    match_cap = REGEX_HEADER_CAPITULO.match(linea)
    if match_cap:
        tipo = match_cap.group(1).capitalize()
        numero = match_cap.group(2)
        extra = match_cap.group(3).strip()
        titulo_completo = f"{tipo} {numero}" + (f" - {extra}" if extra else "")
        nivel = 1 if tipo.upper() in ["CAPÍTULO", "CAPITULO", "TÍTULO", "TITULO"] else 2
        return nivel, titulo_completo

    return None


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


# ---------------------------------------------------------
# 3. EL CORAZÓN HÍBRIDO (spaCy + Unstructured + Regex)
# ---------------------------------------------------------
def limpiar_texto_raw(texto: str) -> str:
    """
    Usa 'unstructured' para separar tablas/listas del texto plano.
    Luego usa 'spaCy' para reconstruir gramaticalmente el texto plano cortado por saltos de línea.
    """
    # 1. Filtro básico de ruido con tus regex
    lineas_limpias = [
        linea.strip() for linea in texto.splitlines() 
        if linea.strip() and not any(p.search(linea) for p in PATRONES_RUIDO)
    ]
    texto_sin_ruido = "\n".join(lineas_limpias)
    
    if not texto_sin_ruido:
        return ""

    # 2. Unstructured: Identifica la naturaleza de cada bloque
    try:
        elementos = partition_text(text=texto_sin_ruido)
    except Exception:
        # Fallback en caso de que unstructured falle con algún caracter raro
        elementos = []

    resultado_final = []

    # 3. Procesamiento específico por tipo de estructura
    if elementos:
        for el in elementos:
            tipo_elemento = type(el).__name__
            
            if tipo_elemento in ["Table", "ListItem"]:
                # Protegemos tablas y listas dejándolas tal cual
                resultado_final.append(str(el))
            else:
                # Es texto narrativo (NarrativeText). Pasamos a spaCy para unir oraciones rotas.
                doc = nlp(str(el))
                parrafos_reconstruidos = []
                
                for oracion in doc.sents:
                    # Remplaza saltos de línea erróneos por espacios dentro de la misma oración
                    oracion_limpia = re.sub(r'\s+', ' ', oracion.text.replace('\n', ' ')).strip()
                    if oracion_limpia:
                        parrafos_reconstruidos.append(oracion_limpia)
                        
                resultado_final.append(" ".join(parrafos_reconstruidos))
    else:
        # Fallback: Si no hay elementos (texto muy corto), usar spacy directo
        doc = nlp(texto_sin_ruido)
        parrafos = [re.sub(r'\s+', ' ', o.text.replace('\n', ' ')).strip() for o in doc.sents]
        resultado_final.append(" ".join(parrafos))

    # Devolver uniendo con doble salto de línea para mantener párrafos limpios
    return "\n\n".join(resultado_final)


def extraer_indice(lineas: list[str]) -> list[str]:
    indice = []
    dentro_indice = False
    for linea in lineas:
        linea_str = linea.strip()
        if REGEX_INDICE.match(linea_str):
            dentro_indice = True
            continue
        if dentro_indice:
            if REGEX_BIBLIOGRAFIA.match(linea_str) or (detectar_encabezado(linea_str) and not REGEX_INDICE.match(linea_str)):
                break
            if not linea_str or linea_str.isdigit():
                continue
            if any(palabra in linea_str for palabra in ["Traducción oficial", "ISO 2015", "derechos reservados", "©"]):
                continue

            limpio = re.sub(r"[|*_#]", "", linea_str).strip()
            if limpio:
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
            if detectar_encabezado(linea_str):
                break
            limpio = re.sub(r"[|*_#]", "", linea_str).strip()
            if limpio:
                if limpio.isdigit() or len(limpio) < 5:
                    continue
                if any(palabra in limpio for palabra in ["Traducción oficial", "ISO", "derechos reservados", "©"]):
                    continue
                if REGEX_PATRON_REFERENCIA.search(limpio) or len(bibliografia) >= 0:
                    bibliografia.append(limpio)
    return bibliografia


def parsear_markdown_a_secciones(filepath: Path) -> dict:
    lineas = filepath.read_text(encoding="utf-8").splitlines()
    titulo_raiz = filepath.stem.split("__", 1)[-1].replace("_", " ").strip()
    if lineas and lineas[0].strip() == "---":
        cierre_frontmatter = next(
            (indice for indice, linea in enumerate(lineas[1:], start=1) if linea.strip() == "---"),
            None,
        )
        if cierre_frontmatter is not None:
            lineas = lineas[cierre_frontmatter + 1:]

    indice = extraer_indice(lineas)
    bibliografia = extraer_bibliografia(lineas)

    secciones: list[dict] = []
    stack: list[tuple[int, str]] = [(1, titulo_raiz or "Documento")]
    buffer: list[str] = []

    def guardar():
        if buffer and stack:
            # Aquí ocurre la magia: El buffer crudo se procesa con unstructured + spacy
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

        if REGEX_INDICE.match(linea_str) or REGEX_BIBLIOGRAFIA.match(linea_str):
            guardar()
            stack.clear()
            omitir_seccion = True
            continue

        encabezado = detectar_encabezado(linea_str)

        if encabezado and omitir_seccion:
            omitir_seccion = False

        if encabezado and not omitir_seccion:
            guardar()
            nivel, titulo = encabezado
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