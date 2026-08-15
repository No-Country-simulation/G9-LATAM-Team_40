"""
Script principal (Orquestador) para la construcción del Grafo y GraphRAG.
Ejecuta la actualización incremental de documentos nuevos o modificados de la Etapa 2.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from settings import settings
from .graph_builder import GraphRAGBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("MAIN")


def cargar_json_seguro(ruta: Path) -> list[dict]:
    if not ruta.exists():
        logger.warning("El archivo no existe: %s", ruta)
        return []
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
    except Exception as e:
        logger.error("Error al leer JSON en %s: %s", ruta, e)
    return []


def ejecutar_construccion_grafo() -> None:
    settings.ensure_dirs()
    logger.info("Iniciando construcción y actualización incremental del Grafo de Conocimiento Global...")

    # Inicializa el constructor, que carga el grafo y los embeddings existentes (si ya existen)
    builder = GraphRAGBuilder(
        ruta_grafo=settings.FILE_GRAFO_JSON,
        ruta_embeddings=settings.FILE_EMBEDDINGS_JSON
    )

    archivos_clasificados = [
        ("ISO", settings.FILE_ISO_CLASIFICADO),
        ("LEYES", settings.FILE_LEYES_CLASIFICADO),
    ]

    total_procesados = 0

    for tipo, ruta_archivo in archivos_clasificados:
        documentos = cargar_json_seguro(ruta_archivo)
        logger.info("Procesando %d documentos del grupo: %s", len(documentos), tipo)

        for doc in documentos:
            try:
                # El nuevo GraphRAGBuilder procesa todo a partir de la estructura del diccionario
                builder.procesar_documento(doc)
                total_procesados += 1
            except Exception as e:
                logger.error("Error procesando documento en el grupo [%s]: %s", tipo, e)

    logger.info("Documentos procesados: %d. Verificando nodos semánticos nuevos para embeddings...", total_procesados)

    # La nueva versión de GraphRAGBuilder identifica automáticamente qué entidades, 
    # conceptos y categorías no tienen embedding, los genera y guarda el store actualizado.
    builder.generar_y_guardar_embeddings()

    # Guarda el grafo consolidado final respetando la estructura JSON estricta (nodos, secciones, etc.)
    builder.guardar_grafo()
    
    logger.info("¡Grafo Global GraphRAG actualizado y guardado con éxito en: %s!", settings.FILE_GRAFO_JSON)
    logger.info("¡Archivo de embeddings consolidado en: %s!", settings.FILE_EMBEDDINGS_JSON)


if __name__ == "__main__":
    # Siempre ejecuta la actualización (el builder maneja internamente la carga incremental)
    ejecutar_construccion_grafo()