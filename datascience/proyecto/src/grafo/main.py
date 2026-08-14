from __future__ import annotations

import json
import logging
from settings import settings
from .graph_builder import GraphRAGBuilder

logger = logging.getLogger("GraphRAG_Etapa3")


def ejecutar_construccion_grafo() -> None:
    """Ejecuta la Etapa 3: Construcción incremental del Grafo de Conocimiento y Embeddings."""
    logger.info("Iniciando construcción del grafo normativo (modo incremental)...")

    # Inicializar constructor de grafo con las rutas centralizadas en settings
    builder = GraphRAGBuilder(
        ruta_grafo=settings.FILE_GRAFO_JSON,
        ruta_embeddings=settings.FILE_EMBEDDINGS_JSON,
    )

    # Definir los archivos clasificados de entrada (ISO y Leyes)
    archivos_a_procesar = [
        ("ISO", settings.FILE_ISO_CLASIFICADO),
        ("LEYES", settings.FILE_LEYES_CLASIFICADO),
    ]

    total_nuevos_procesados = 0

    for tipo, ruta_json in archivos_a_procesar:
        if not ruta_json.exists():
            logger.warning("No se encontró el archivo clasificado: %s. Se omite '%s'.", ruta_json, tipo)
            continue

        try:
            documentos = json.loads(ruta_json.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("Error al leer %s: %s", ruta_json, e)
            continue

        logger.info("Revisando %d documentos en '%s' para actualización incremental...", len(documentos), tipo)

        for idx, doc in enumerate(documentos):
            document_id, _ = builder.obtener_identificador(doc, tipo, idx)

            # VALIDACIÓN INCREMENTAL: Si ya está en el grafo, se omite
            if builder.documento_ya_en_grafo(document_id):
                continue

            logger.info("Añadiendo nuevo documento al grafo: ID='%s' (%s)", document_id, tipo)
            
            # 1. Procesar nodos, secciones, conceptos y relaciones en el grafo
            builder.procesar_documento(doc, tipo, idx)

            # 2. Recolectar y generar embeddings solo para las entidades nuevas de este documento
            entidades_nuevas = builder.recolectar_entidades_nuevas(doc)
            if entidades_nuevas:
                builder.generar_y_guardar_embeddings(entidades_nuevas)

            total_nuevos_procesados += 1

    if total_nuevos_procesados > 0:
        # Guardar cambios persistentes en disco
        builder.guardar_grafo()
        builder.guardar_store_embeddings()
        logger.info("Grafo actualizado incrementalmente. Se agregaron %d documentos nuevos.", total_nuevos_procesados)
    else:
        logger.info("El grafo ya está actualizado. No se encontraron documentos nuevos pendientes.")

    logger.info("Etapa 3 completada con éxito.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ejecutar_construccion_grafo()