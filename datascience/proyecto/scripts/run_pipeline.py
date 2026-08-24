"""Orquestador de etapas 0–4 y builds privados aislados."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROYECTO_DIR = SCRIPTS_DIR.parent
SRC_DIR = PROYECTO_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("PipelineOrchestrator")


def ejecutar_etapa_0_limpieza():
    from clean.clean import ejecutar_pipeline
    ejecutar_pipeline()


def ejecutar_etapa_1_extraccion():
    from extraccion.pipeline import Pipeline
    Pipeline(settings).ejecutar()


def ejecutar_etapa_2_clasificacion():
    from clasificacion.main import ejecutar_clasificacion
    ejecutar_clasificacion()


def ejecutar_etapa_3_grafo():
    from grafo.main import ejecutar_construccion_grafo
    ejecutar_construccion_grafo()


def ejecutar_etapa_4_rag(pregunta: str | None = None):
    from indexacion.main import PipelineGraphRAG, imprimir_resultado
    pipeline = PipelineGraphRAG()
    if pregunta:
        imprimir_resultado(pregunta, pipeline.responder_consulta(pregunta))
        return
    while True:
        try:
            value = input("Pregunta > ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if value.lower() in {"salir", "exit", "q"}:
            return
        if value:
            imprimir_resultado(value, pipeline.responder_consulta(value))


def ejecutar_build():
    """Run only stages 0–3 in the caller-provided ROOT_DIR workspace."""
    settings.ensure_dirs()
    ejecutar_etapa_0_limpieza()
    ejecutar_etapa_1_extraccion()
    ejecutar_etapa_2_clasificacion()
    ejecutar_etapa_3_grafo()


def main():
    parser = argparse.ArgumentParser(description="Orquestador GraphRAG")
    parser.add_argument(
        "--etapa",
        choices=["0", "1", "2", "3", "4", "build", "all"],
        default="all",
    )
    parser.add_argument("--pregunta", default=None)
    args = parser.parse_args()
    settings.ensure_dirs()
    if args.etapa in {"1", "2", "4", "build", "all"}:
        settings.validate_keys()
    if args.etapa == "all":
        ejecutar_etapa_0_limpieza()
        ejecutar_etapa_1_extraccion()
        ejecutar_etapa_2_clasificacion()
        ejecutar_etapa_3_grafo()
        ejecutar_etapa_4_rag(args.pregunta)
    elif args.etapa == "build":
        ejecutar_build()
    elif args.etapa == "0":
        ejecutar_etapa_0_limpieza()
    elif args.etapa == "1":
        ejecutar_etapa_1_extraccion()
    elif args.etapa == "2":
        ejecutar_etapa_2_clasificacion()
    elif args.etapa == "3":
        ejecutar_etapa_3_grafo()
    else:
        ejecutar_etapa_4_rag(args.pregunta)


if __name__ == "__main__":
    main()
