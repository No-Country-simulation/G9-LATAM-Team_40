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

    builder = GraphRAGBuilder(ruta_grafo=settings.FILE_GRAFO_JSON, ruta_embeddings=settings.FILE_EMBEDDINGS_JSON)

    fuentes = [(settings.FILE_ISO_EXTRACCION, settings.FILE_ISO_CLASIFICADO),
                (settings.FILE_LEYES_EXTRACCION, settings.FILE_LEYES_CLASIFICADO)]
    total_procesados = 0

    for ruta_extraccion, ruta_clasificacion in fuentes:
        documentos = cargar_json_seguro(ruta_extraccion)
        clasificaciones = cargar_json_seguro(ruta_clasificacion)

        documentos_por_id = {
            doc["documento_id"]: doc
            for doc in documentos
            if doc.get("documento_id")
        }

        clasificaciones_por_id = {
            doc["documento_id"]: doc
            for doc in clasificaciones
            if doc.get("documento_id")
        }

        ids_sin_clasificacion = documentos_por_id.keys() - clasificaciones_por_id.keys()
        ids_sin_extraccion = clasificaciones_por_id.keys() - documentos_por_id.keys()

        for documento_id in ids_sin_clasificacion:
            logger.warning(
                "El documento %s tiene extracción, pero no clasificación.",
                documento_id,
            )

        for documento_id in ids_sin_extraccion:
            logger.warning(
                "El documento %s tiene clasificación, pero no extracción.",
                documento_id,
            )

        categorias_por_nombre = {}
        for doc in clasificaciones:
            documento_id = doc.get("documento_id")
            if not documento_id:
                continue
            for clasif in doc.get("clasificaciones", []):
                categoria = clasif.get("categoria")
                if categoria:
                    categorias_por_nombre.setdefault(categoria, []).append({
                        "documento_id": documento_id,
                        "confianza": clasif.get("confianza", 1.0)
                    })


        for categoria, documentos_categoria in categorias_por_nombre.items():
            resultados_json_secciones = [
                {
                    "documento_id": documento_id,
                    "secciones": [
                        {
                            "titulo": seccion.get("titulo"),
                            "nivel": seccion.get("nivel"),
                            "ruta_jerarquica": seccion.get("ruta_jerarquica", []),
                            "relaciones": seccion.get("relaciones", [])
                        }
                        for seccion in documentos_por_id[documento_id].get("secciones", [])
                    ]
                }
                for documento_id in {item["documento_id"] for item in documentos_categoria}
                if documento_id in documentos_por_id
            ]

            builder.procesar_categoria(categoria, resultados_json_secciones, documentos_categoria)
            total_procesados += len(resultados_json_secciones)

    logger.info("Documentos procesados: %d. Verificando nodos semánticos nuevos para embeddings...", total_procesados)

    # La versión de GraphRAGBuilder identifica automáticamente qué entidades, 
    # conceptos y categorías no tienen embedding, los genera y guarda el store actualizado.
    builder.generar_y_guardar_embeddings()

    # Guarda el grafo consolidado final respetando la estructura JSON estricta
    builder.guardar_grafo()
    
    logger.info("¡Grafo Global GraphRAG actualizado y guardado con éxito en: %s!", settings.FILE_GRAFO_JSON)
    logger.info("¡Archivo de sembeddings consolidado en: %s!", settings.FILE_EMBEDDINGS_JSON)
    

if __name__ == "__main__":
    # Siempre ejecuta la actualización (el builder maneja internamente la carga incremental)
    ejecutar_construccion_grafo()