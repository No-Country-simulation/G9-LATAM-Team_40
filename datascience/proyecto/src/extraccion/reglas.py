"""Carga de las reglas de dominio (diccionario, roles, stopwords, relaciones verbales y glosario)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .normalizacion import normalizar_texto

@dataclass(frozen=True)
class ReglasDominio:
    diccionario_dominio: dict[str, list[str]]
    roles_legales: list[str]
    stopwords_custom: set[str]
    relaciones_verbales: dict[str, list[str]]
    mapa_relaciones: dict[str, str]
    glosario: dict[str, dict[str, str]]


def cargar_reglas(
    config_path: Path,
    relations_path: Path,
    glosario_path: Path 
) -> ReglasDominio:

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)


    with open(relations_path, "r", encoding="utf-8") as f:
        relations_config = json.load(f)


    glosario_data = {}

    if glosario_path and glosario_path.exists():

        with open(glosario_path, "r", encoding="utf-8") as f:
            raw_glosario = json.load(f)

        glosario_data = {
            normalizar_texto(k): v
            for k, v in raw_glosario.items()
        }


    diccionario_dominio = config.get(
        "DICCIONARIO_DOMINIO",
        {}
    )

    roles_legales = config.get(
        "ROLES_LEGALES",
        []
    )

    stopwords_custom = set(
        config.get(
            "STOPWORDS_CUSTOM",
            []
        )
    )

    relaciones_verbales = relations_config.get(
        "RELACIONES_VERBALES",
        {}
    )


    mapa_relaciones = {
        normalizar_texto(verbo): relacion
        for relacion, verbos in relaciones_verbales.items()
        for verbo in verbos
    }


    return ReglasDominio(
        diccionario_dominio=diccionario_dominio,
        roles_legales=roles_legales,
        stopwords_custom=stopwords_custom,
        relaciones_verbales=relaciones_verbales,
        mapa_relaciones=mapa_relaciones,
        glosario=glosario_data
    )