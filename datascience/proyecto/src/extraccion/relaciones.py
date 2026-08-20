"""Relaciones por dependencia sintáctica (spaCy) y fusión de resultados reglas + LLM."""
from __future__ import annotations

from .normalizacion import normalizar_key, normalizar_texto

DEPS_SUJETO = ("nsubj", "nsubj:pass", "expl", "expl:pass")
DEPS_OBJETO = ("obj", "obl", "pobj", "iobj", "attr")


def _expandir_conjuntos(tokens):
    """Incluye conjunciones coordinadas (dep_='conj') de cada token dado, para
    capturar sujetos/objetos coordinados como 'el empleador y el trabajador'
    que de otro modo quedan colgando fuera del árbol de hijos directos del verbo."""
    expandido = list(tokens)
    for t in tokens:
        expandido.extend([h for h in t.children if h.dep_ == "conj"])
    return expandido


def extraer_relaciones_spacy(doc, mapa_relaciones: dict[str, str]) -> list[dict]:
    relaciones = []
    for token in doc:
        if token.pos_ != "VERB":
            continue

        verbo = normalizar_texto(token.lemma_)
        if verbo not in mapa_relaciones:
            continue

        # FIX #1: detectar negación del verbo. Sin esto, "no debe informar" y
        # "debe informar" generaban la misma tripleta, fusionando obligaciones
        # con prohibiciones en el grafo.
        negado = any(h.dep_ == "neg" for h in token.children)
        relacion_tag = mapa_relaciones[verbo]
        if negado:
            relacion_tag = f"NO_{relacion_tag}"

        sujetos = _expandir_conjuntos([h for h in token.children if h.dep_ in DEPS_SUJETO])
        objetos = _expandir_conjuntos([h for h in token.children if h.dep_ in DEPS_OBJETO])

        for sujeto in sujetos:
            for objeto in objetos:
                sujeto_texto = " ".join(x.text for x in sujeto.subtree)
                objeto_texto = " ".join(x.text for x in objeto.subtree)

                if len(sujeto_texto) < 2 or len(objeto_texto) < 2:
                    continue

                relaciones.append({
                    "sujeto": sujeto_texto,
                    "relacion": relacion_tag,
                    "objeto": objeto_texto,
                    "tipo_relacion": "LEGAL",
                    "verbo_detectado": verbo,
                    "origen": "spacy_dependency",
                    "confianza": 0.85,
                    "contexto": token.sent.text,
                    "negado": negado,
                })
    return relaciones


def enriquecer_relaciones(relaciones: list[dict], entidades: list[dict]) -> list[dict]:
    indice = {normalizar_key(ent["texto"]): ent for ent in entidades}
    for relacion in relaciones:
        sujeto_key = normalizar_key(relacion["sujeto"])
        objeto_key = normalizar_key(relacion["objeto"])

        if sujeto_key in indice:
            relacion["sujeto_tipo"] = indice[sujeto_key]["tipo"]
            relacion["sujeto_canonical"] = indice[sujeto_key]["canonical"]

        if objeto_key in indice:
            relacion["objeto_tipo"] = indice[objeto_key]["tipo"]
            relacion["objeto_canonical"] = indice[objeto_key]["canonical"]

    return relaciones


def seccion_es_relevante(
    texto: str,
    entidades_dominio: list[dict],
    mapa_relaciones: dict[str, str],
    conceptos: list[dict] | None = None,
) -> bool:
    """Filtro barato: llama al LLM si hay señal de entidad de dominio, algún
    verbo relevante presente en el texto, o (FIX #3) si YAKE encontró conceptos
    con score alto — señal de contenido sustantivo aunque no use el vocabulario
    exacto del diccionario de dominio ni los verbos catalogados."""
    if entidades_dominio:
        return True
    texto_norm = normalizar_texto(texto)
    if any(verbo in texto_norm for verbo in mapa_relaciones):
        return True
    if conceptos and any(c["score"] > 0.6 for c in conceptos):
        return True
    return False


def merge_entidades(ent_llm: list[dict], ent_reglas: list[dict], texto_seccion: str = "") -> list[dict]:
    indice: dict[str, dict] = {}
    texto_norm = normalizar_texto(texto_seccion) if texto_seccion else ""

    for e in ent_llm:
        key = normalizar_key(e["texto"])
        # FIX #2: verificar que la entidad devuelta por el LLM exista literalmente
        # en el texto fuente. No hay grounding real (offsets), pero esta
        # verificación barata detecta alucinaciones/paráfrasis del LLM sin
        # necesidad de migrar a una librería con grounding nativo.
        verificado = (normalizar_texto(e["texto"]) in texto_norm) if texto_norm else None
        indice[key] = {
            "texto": e["texto"],
            "texto_normalizado": normalizar_texto(e["texto"]),
            "canonical": e["texto"].upper(),
            "tipo": e["tipo"],
            "origen": "deepseek",
            "verificado": verificado,
        }

    for e in ent_reglas:
        key = normalizar_key(e["texto"])
        if key not in indice:
            e = dict(e)
            e["origen"] = "solo_diccionario_dominio"
            e.setdefault("verificado", True)  # viene de regex/diccionario: está en el texto por definición
            indice[key] = e
        else:
            indice[key]["origen"] = "ambos_confirmado"
            # Preferimos 'canonical' y 'tipo' del diccionario de dominio (taxonomía controlada).
            indice[key]["canonical"] = e.get("canonical", indice[key]["canonical"])
            indice[key]["tipo"] = e.get("tipo", indice[key]["tipo"])
            indice[key]["verificado"] = True  # confirmada también por reglas deterministas

    return list(indice.values())


def merge_relaciones(rel_llm: list[dict], rel_spacy: list[dict]) -> list[dict]:
    def firma(r):
        return (normalizar_key(r["sujeto"]), r["relacion"], normalizar_key(r["objeto"]))

    indice: dict[tuple, dict] = {}

    for r in rel_llm:
        r = dict(r)
        r["origen"] = "deepseek"
        r["confianza"] = 0.7
        indice[firma(r)] = r

    for r in rel_spacy:
        f = firma(r)
        if f not in indice:
            indice[f] = r
        else:
            indice[f]["origen"] = "ambos_confirmado"
            indice[f]["confianza"] = 0.95

    return list(indice.values())