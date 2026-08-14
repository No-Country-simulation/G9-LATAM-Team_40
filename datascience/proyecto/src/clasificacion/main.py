"""Módulo principal de orquestación para la Etapa 2 (Clasificación)."""

from __future__ import annotations

import logging
from settings import settings
from storage.storage import StorageManager
from .classifier import DocumentClassifier

logger = logging.getLogger(__name__)


def ejecutar_clasificacion() -> None:
    """Ejecuta el flujo completo de la Etapa 2: Clasificación y Taxonomía."""
    settings.validate_keys()
    storage = StorageManager(settings)

    info_taxonomia, nombres_a_id, lista_nombres_categorias = storage.cargar_taxonomia()
    logger.info(
        "Taxonomía cargada: %d categorías (run_id: %s)",
        len(lista_nombres_categorias),
        info_taxonomia.get("run_id"),
    )

    classifier = DocumentClassifier(settings, lista_nombres_categorias)
    
    # Valida y asegura los directorios de salida
    settings.SALIDA_JSON_DIR.mkdir(parents=True, exist_ok=True)

    # Itera sobre los archivos de entrada configurados (ISO y LEYES)
    for tipo, ruta in settings.INPUT_FILES_MAP.items():
        if not ruta.exists():
            logger.warning("No existe el archivo de entrada: %s. Se omite '%s'.", ruta, tipo)
            continue

        import json
        lista_docs = json.loads(ruta.read_text(encoding="utf-8"))
        logger.info("Procesando tipo '%s': %d documentos en %s", tipo, len(lista_docs), ruta.name)

        # Definir ruta de salida correspondiente según settings
        path_salida = settings.FILE_ISO_CLASIFICADO if tipo == "ISO" else settings.FILE_LEYES_CLASIFICADO
        
        ya_clasificados = storage.cargar_salida_previa(path_salida)
        storage.respaldar_salida_anterior(path_salida)

        pendientes = []
        resultado_final = []

        for idx, doc in enumerate(lista_docs):
            identificador = (
                doc.get("documento_id")
                or doc.get("metadata", {}).get("archivo")
                or f"{tipo}_{idx}"
            )
            previo = ya_clasificados.get(identificador)

            # Verifica si ya fue clasificado previamente usando exclusivamente 'clasificacion_llm'
            if previo and previo.get("clasificacion_llm"):
                resultado_final.append(previo)
                continue

            titulo = doc.get("documento_nombre") or identificador
            titulos_secciones = [
                s.get("titulo", "").strip()
                for s in doc.get("secciones", [])
                if isinstance(s, dict) and s.get("titulo", "").strip()
            ]
            pendientes.append(
                {
                    "documento_id": identificador,
                    "titulo_documento": titulo,
                    "titulos_secciones": titulos_secciones,
                    "doc_original": doc,
                }
            )

        logger.info("Documentos omitidos (ya clasificados): %d", len(resultado_final))
        logger.info("Documentos pendientes de clasificar: %d", len(pendientes))

        if not pendientes:
            logger.info("No hay documentos pendientes para '%s'.", tipo)
            storage.guardar_json_atomico(path_salida, resultado_final)
            continue

        lote_size = settings.DOCUMENTOS_POR_LOTE
        total_lotes = -(-len(pendientes) // lote_size)

        for idx_lote, i in enumerate(range(0, len(pendientes), lote_size), start=1):
            lote = pendientes[i : i + lote_size]
            logger.info("Procesando Lote %d/%d (%d documentos)...", idx_lote, total_lotes, len(lote))

            resultado_lote = classifier.clasificar_lote(lote)
            mapa_resultado = {r["documento_id"]: r for r in resultado_lote}

            for item in lote:
                r = mapa_resultado.get(
                    item["documento_id"],
                    {"categorias_asignadas": [], "confianzas": []},
                )

                clasificaciones = [
                    {
                        "cluster_id": nombres_a_id.get(nombre, nombre),
                        "concepto": nombre,
                        "categoria": nombre,
                        "confianza": conf,
                    }
                    for nombre, conf in zip(r.get("categorias_asignadas", []), r.get("confianzas", []))
                    if nombre in nombres_a_id
                ]

                from datetime import datetime
                etiqueta = {
                    "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "fecha_procesado": datetime.now().isoformat(),
                    "tipo_documento": tipo,
                    "clasificaciones": clasificaciones,
                    "revisar_manual": len(clasificaciones) == 0,
                    "metodo": "LLM_puro_titulos",
                    "modelo_llm": settings.DEEPSEEK_MODEL,
                    "taxonomia_run_id": info_taxonomia.get("run_id", "unknown"),
                }

                doc_clasificado = dict(item["doc_original"])
                doc_clasificado["clasificacion_llm"] = etiqueta
                resultado_final.append(doc_clasificado)

            storage.guardar_json_atomico(path_salida, resultado_final)

        logger.info("Guardado final completado para '%s' -> %s", tipo, path_salida.resolve())

    logger.info("Clasificación completa exitosamente.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ejecutar_clasificacion()