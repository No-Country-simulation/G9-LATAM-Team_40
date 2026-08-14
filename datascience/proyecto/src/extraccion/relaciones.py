"""Relaciones por dependencia sintáctica (spaCy) y fusión de resultados reglas + LLM."""
from __future__ import annotations

from .normalizacion import normalizar_key, normalizar_texto


def extraer_relaciones_spacy(doc, mapa_relaciones: dict[str, str]) -> list[dict]:
    relaciones = []
    for token in doc:
        if token.pos_ != "VERB":
            continue

        verbo = normalizar_texto(token.lemma_)
        if verbo not in mapa_relaciones:
            continue

        sujetos = [h for h in token.children if h.dep_ in ("nsubj", "nsubj:pass")]
        objetos = [h for h in token.children if h.dep_ in ("obj", "obl", "pobj", "iobj", "attr")]

        for sujeto in sujetos:
            for objeto in objetos:
                sujeto_texto = " ".join(x.text for x in sujeto.subtree)
                objeto_texto = " ".join(x.text for x in objeto.subtree)

                if len(sujeto_texto) < 2 or len(objeto_texto) < 2:
                    continue

                relaciones.append({
                    "sujeto": sujeto_texto,
                    "relacion": mapa_relaciones[verbo],
                    "objeto": objeto_texto,
                    "tipo_relacion": "LEGAL",
                    "verbo_detectado": verbo,
                    "origen": "spacy_dependency",
                    "confianza": 0.85,
                    "contexto": token.sent.text,
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


def seccion_es_relevante(texto: str, entidades_dominio: list[dict], mapa_relaciones: dict[str, str]) -> bool:
    """Filtro barato: solo llama al LLM si hay señal de entidad de dominio
    o algún verbo relevante presente en el texto."""
    if entidades_dominio:
        return True
    texto_norm = normalizar_texto(texto)
    return any(verbo in texto_norm for verbo in mapa_relaciones)


def merge_entidades(ent_llm: list[dict], ent_reglas: list[dict]) -> list[dict]:
    indice: dict[str, dict] = {}

    for e in ent_llm:
        key = normalizar_key(e["texto"])
        indice[key] = {
            "texto": e["texto"],
            "texto_normalizado": normalizar_texto(e["texto"]),
            "canonical": e["texto"].upper(),
            "tipo": e["tipo"],
            "origen": "deepseek",
        }

    for e in ent_reglas:
        key = normalizar_key(e["texto"])
        if key not in indice:
            e = dict(e)
            e["origen"] = "solo_diccionario_dominio"
            indice[key] = e
        else:
            indice[key]["origen"] = "ambos_confirmado"
            # Preferimos 'canonical' y 'tipo' del diccionario de dominio (taxonomía controlada).
            indice[key]["canonical"] = e.get("canonical", indice[key]["canonical"])
            indice[key]["tipo"] = e.get("tipo", indice[key]["tipo"])

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
