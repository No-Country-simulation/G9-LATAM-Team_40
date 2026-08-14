"""
Orquestador principal del pipeline KNOGMENT_NAYE.
Ejecuta de manera secuencial o individual las etapas del sistema GraphRAG:
  - Etapa 0: Limpieza previa de documentos.
  - Etapa 1: Extracción de entidades y relaciones (LLM + NLP).
  - Etapa 2: Descubrimiento de taxonomía y clasificación.
  - Etapa 3: Construcción del Grafo de Conocimiento y Embeddings.
  - Etapa 4: Recuperación RAG / Consulta final.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# ------------------------------------------------------------------------------
# RESOLUCIÓN DINÁMICA DE RUTAS DE IMPORTACIÓN
# ------------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent
PROYECTO_DIR = SCRIPTS_DIR.parent
SRC_DIR = PROYECTO_DIR / "src"

# Garantizar que Python encuentre 'settings' y los módulos dentro de src/
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from extraccion.pipeline import Pipeline
from settings import settings

# ------------------------------------------------------------------------------
# CONFIGURACIÓN DE LOGGING
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PipelineOrchestrator")


# ------------------------------------------------------------------------------
# EJECUCIÓN POR ETAPAS
# ------------------------------------------------------------------------------
def ejecutar_etapa_0_limpieza():
    logger.info("=== [ETAPA 0] Iniciando Limpieza de Texto ===")
    from clean.clean import ejecutar_pipeline
    ejecutar_pipeline()
    logger.info("=== [ETAPA 0] Limpieza completada con éxito. ===")


def ejecutar_etapa_1_extraccion():
    pipeline = Pipeline(settings)
    pipeline.ejecutar()


def ejecutar_etapa_2_clasificacion():
    logger.info("=== [ETAPA 2] Iniciando Taxonomía y Clasificación ===")
    from clasificacion.main import ejecutar_clasificacion
    ejecutar_clasificacion()
    logger.info("=== [ETAPA 2] Clasificación completada. ===")


def ejecutar_etapa_3_grafo():
    logger.info("=== [ETAPA 3] Construyendo Grafo de Conocimiento y Embeddings ===")
    from grafo.main import ejecutar_construccion_grafo
    ejecutar_construccion_grafo()
    logger.info("=== [ETAPA 3] Grafo generado correctamente. ===")


def ejecutar_etapa_4_rag(pregunta: str | None = None):
    logger.info("=== [ETAPA 4] Búsqueda y Generación RAG ===")
    from indexacion.main import ejecutar_etapa_4

    if pregunta:
        logger.info("Ejecutando consulta puntual: '%s'", pregunta)
        respuesta = ejecutar_etapa_4(pregunta)
        print("\n" + "=" * 80)
        print("RESPUESTA OBTENIDA:")
        print("=" * 80)
        print(respuesta)
        print("=" * 80)
    else:
        # Modo interactivo CLI si no se provee una pregunta
        print("\n" + "=" * 80)
        print(" SISTEMA GRAPHRAG INTERACTIVO (Escribe 'salir' para finalizar)")
        print("=" * 80 + "\n")
        while True:
            try:
                p = input("\n Pregunta > ").strip()
                if not p:
                    continue
                if p.lower() in ["salir", "exit", "q"]:
                    print("\nSesión finalizada.")
                    break
                
                resp = ejecutar_etapa_4(p)
                print("\n" + "-" * 80)
                print("RESPUESTA:")
                print("-" * 80)
                print(resp)
                print("-" * 80)
            except KeyboardInterrupt:
                print("\n\nInterrumpido por el usuario. Saliendo...")
                break


# ------------------------------------------------------------------------------
# PUNTO DE ENTRADA CLI
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Orquestador General de Pipeline GraphRAG Normativo"
    )
    parser.add_argument(
        "--etapa",
        type=str,
        choices=["0", "1", "2", "3", "4", "all"],
        default="all",
        help="Etapa específica a ejecutar (0: Limpieza, 1: Extracción, 2: Clasificación, 3: Grafo, 4: RAG, all: Todo el pipeline)",
    )
    parser.add_argument(
        "--pregunta",
        type=str,
        default=None,
        help="Pregunta específica para ejecutar únicamente la Etapa 4 en modo batch",
    )

    args = parser.parse_args()

    # 1. Asegurar la existencia de directorios base
    settings.ensure_dirs()

    # 2. Validar API Keys si se requiere procesamiento LLM
    if args.etapa in ["1", "2", "4", "all"]:
        settings.validate_keys()

    # 3. Flujo de Ejecución
    if args.etapa == "all":
        logger.info("🚀 INICIANDO EJECUCIÓN DEL PIPELINE COMPLETO 🚀")
        ejecutar_etapa_0_limpieza()
        ejecutar_etapa_1_extraccion()
        ejecutar_etapa_2_clasificacion()
        ejecutar_etapa_3_grafo()
        ejecutar_etapa_4_rag(args.pregunta)
        logger.info("✅ PIPELINE COMPLETO FINALIZADO EXITOSAMENTE")

    elif args.etapa == "0":
        ejecutar_etapa_0_limpieza()
    elif args.etapa == "1":
        ejecutar_etapa_1_extraccion()
    elif args.etapa == "2":
        ejecutar_etapa_2_clasificacion()
    elif args.etapa == "3":
        ejecutar_etapa_3_grafo()
    elif args.etapa == "4":
        ejecutar_etapa_4_rag(args.pregunta)


if __name__ == "__main__":
    main()