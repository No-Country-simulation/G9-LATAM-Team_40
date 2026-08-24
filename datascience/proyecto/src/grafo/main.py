"""Construcción del grafo consolidado para las etapas 0–3."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from settings import settings
from .graph_builder import GraphRAGBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("MAIN")


def cargar_json_seguro(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else [data]
    except Exception as exc:
        logger.error("Error al leer JSON en %s: %s", ruta, exc)
        return []


def _asegurar_clasificacion(documentos: list[dict], clasificaciones: list[dict]) -> tuple[list[dict], bool]:
    por_id = {item.get("documento_id"): item for item in clasificaciones if item.get("documento_id")}
    changed = False
    for documento in documentos:
        documento_id = documento.get("documento_id")
        if not documento_id:
            continue
        item = por_id.get(documento_id)
        if item is None:
            item = {"documento_id": documento_id, "tipo_documento": documento.get("tipo_documento", ""), "clasificaciones": []}
            clasificaciones.append(item)
            por_id[documento_id] = item
            changed = True
        if not item.get("clasificaciones"):
            item["clasificaciones"] = [{
                "cluster_id": "CAT_SINCATEGORIA",
                "categoria": "Sin categoría",
                "confianza": 0.0,
                "palabras_claves": [],
            }]
            changed = True
    return clasificaciones, changed


def ejecutar_construccion_grafo() -> None:
    settings.ensure_dirs()
    builder = GraphRAGBuilder(
        ruta_grafo=settings.FILE_GRAFO_JSON,
        ruta_embeddings=settings.FILE_EMBEDDINGS_JSON,
    )
    fuentes = [
        (settings.FILE_ISO_EXTRACCION, settings.FILE_ISO_CLASIFICADO),
        (settings.FILE_LEYES_EXTRACCION, settings.FILE_LEYES_CLASIFICADO),
    ]
    total_procesados = 0
    for ruta_extraccion, ruta_clasificacion in fuentes:
        documentos = cargar_json_seguro(ruta_extraccion)
        clasificaciones = cargar_json_seguro(ruta_clasificacion)
        clasificaciones, changed = _asegurar_clasificacion(documentos, clasificaciones)
        if changed:
            ruta_clasificacion.parent.mkdir(parents=True, exist_ok=True)
            ruta_clasificacion.write_text(
                json.dumps(clasificaciones, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        documentos_por_id = {
            doc["documento_id"]: doc for doc in documentos if doc.get("documento_id")
        }
        categorias_por_nombre: dict[str, list[dict]] = {}
        for item in clasificaciones:
            documento_id = item.get("documento_id")
            if documento_id not in documentos_por_id:
                continue
            for clasif in item.get("clasificaciones", []):
                categoria = str(clasif.get("categoria") or "Sin categoría").strip()
                categorias_por_nombre.setdefault(categoria, []).append({
                    "documento_id": documento_id,
                    "confianza": float(clasif.get("confianza", 0.0)),
                })
        for categoria, documentos_categoria in categorias_por_nombre.items():
            ids = {item["documento_id"] for item in documentos_categoria}
            secciones = [
                {
                    "documento_id": documento_id,
                    "secciones": [
                        {
                            "titulo": section.get("titulo"),
                            "nivel": section.get("nivel"),
                            "ruta_jerarquica": section.get("ruta_jerarquica", []),
                            "relaciones": section.get("relaciones", []),
                        }
                        for section in documentos_por_id[documento_id].get("secciones", [])
                    ],
                }
                for documento_id in ids
            ]
            builder.procesar_categoria(categoria, secciones, documentos_categoria)
            total_procesados += len(secciones)
    builder.generar_y_guardar_embeddings()
    builder.guardar_grafo()
    logger.info("Grafo actualizado: %d documentos", total_procesados)


if __name__ == "__main__":
    ejecutar_construccion_grafo()
