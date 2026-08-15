"""
Módulo principal de orquestación para la Etapa 2 (Clasificación).

Sin memoria de corridas anteriores: cada ejecución procesa TODOS los
documentos desde cero y sobreescribe el archivo de salida completo.
No hay reutilización de clasificaciones previas ni backups.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import datetime

from settings import settings
from storage.storage import StorageManager
from .classifier import DocumentClassifier

logger = logging.getLogger(__name__)


def normalizar_texto(texto: str) -> str:
    """Normaliza un texto para compararlo sin tildes, minúsculas ni espacios extra."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def generar_slug_categoria(nombre: str, slugs_usados: set[str]) -> str:
    """Genera un slug único en MAYÚSCULAS para usar como cluster_id de una categoría nueva."""
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9]+", "_", sin_acentos).strip("_").upper()[:60]
    if not slug:
        slug = "CATEGORIA"

    slug_final, contador = slug, 2
    while slug_final in slugs_usados:
        slug_final = f"{slug}_{contador}"
        contador += 1

    slugs_usados.add(slug_final)
    return slug_final


def ejecutar_clasificacion() -> None:
    settings.validate_keys()
    storage = StorageManager(settings)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("Iniciando Etapa 2 - Clasificación (sin memoria). run_id=%s", run_id)

    # 1. Cargar taxonomía
    info_taxonomia, nombres_a_id, lista_nombres_categorias = storage.cargar_taxonomia()
    if not lista_nombres_categorias:
        raise RuntimeError("No se encontró ninguna categoría en la taxonomía. Ejecuta primero la Etapa 1.")

    logger.info("Taxonomía cargada: %d categorías", len(lista_nombres_categorias))

    mapa_normalizado_id = {
        normalizar_texto(nombre): cluster_id
        for nombre, cluster_id in nombres_a_id.items()
    }

    # Slugs ya usados en la taxonomía, para no colisionar al crear categorías nuevas.
    slugs_usados = set(info_taxonomia.get("categorias", {}).keys())

    classifier = DocumentClassifier(settings, lista_nombres_categorias)
    settings.SALIDA_JSON_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Procesar cada tipo de documento
    for tipo, ruta in settings.INPUT_FILES_MAP.items():
        if not ruta.exists():
            logger.warning("No existe archivo de entrada para tipo=%s: %s", tipo, ruta)
            continue

        tipo_normalizado = tipo.upper().strip()
        if tipo_normalizado == "ISO":
            path_salida = settings.FILE_ISO_CLASIFICADO
        elif tipo_normalizado == "LEYES":
            path_salida = settings.FILE_LEYES_CLASIFICADO
        else:
            logger.warning("Tipo de documento no reconocido: %s. Se omite.", tipo)
            continue

        lista_docs = json.loads(ruta.read_text(encoding="utf-8"))
        logger.info("Procesando tipo: %s | Documentos encontrados: %d", tipo_normalizado, len(lista_docs))

        # Sin memoria: se procesan TODOS los documentos, siempre.
        resultado_actual: list[dict] = []

        pendientes = []
        for idx, doc in enumerate(lista_docs):
            identificador = (
                doc.get("documento_id")
                or doc.get("metadata", {}).get("archivo")
                or f"{tipo_normalizado}_{idx}"
            )

            titulo = doc.get("documento_nombre") or identificador
            titulos_secciones = [
                s.get("titulo", "").strip()
                for s in doc.get("secciones", [])
                if isinstance(s, dict) and s.get("titulo", "").strip()
            ]

            pendientes.append({
                "documento_id": identificador,
                "titulo_documento": titulo,
                "titulos_secciones": titulos_secciones,
                "doc_original": doc,
            })

        # 3. Procesamiento por lotes
        lote_size = settings.DOCUMENTOS_POR_LOTE
        for idx_lote, i in enumerate(range(0, len(pendientes), lote_size), start=1):
            lote = pendientes[i : i + lote_size]
            logger.info("Procesando lote %d: %d documentos", idx_lote, len(lote))

            resultado_lote = classifier.clasificar_lote(lote)
            mapa_resultado = {r.get("documento_id"): r for r in resultado_lote if r.get("documento_id")}

            for item in lote:
                doc_id = item["documento_id"]
                r = mapa_resultado.get(doc_id, {"categorias_asignadas": [], "confianzas": []})

                categorias = r.get("categorias_asignadas", [])
                confianzas = r.get("confianzas", [])
                clasificaciones = []
                clusters_vistos = set()

                for posicion, cat_nombre in enumerate(categorias):
                    nombre_limpio = str(cat_nombre).strip()
                    if not nombre_limpio:
                        continue

                    try:
                        confianza = float(confianzas[posicion]) if posicion < len(confianzas) else 0.0
                    except (TypeError, ValueError):
                        confianza = 0.0

                    if not (0.0 <= confianza <= 1.0):
                        logger.warning("Confianza inválida %.3f. Doc=%s Cat=%s", confianza, doc_id, nombre_limpio)
                        continue

                    if confianza < settings.UMBRAL_CONFIANZA:
                        continue

                    nombre_norm = normalizar_texto(nombre_limpio)
                    cluster_id = mapa_normalizado_id.get(nombre_norm)

                    if cluster_id is None:
                        # Categoría nueva propuesta por el LLM: se crea y se agrega a la taxonomía.
                        cluster_id = generar_slug_categoria(nombre_limpio, slugs_usados)
                        info_taxonomia.setdefault("categorias", {})[cluster_id] = {
                            "nombre": nombre_limpio,
                            "descripcion": f"Categoría autogenerada por el clasificador (detectada en '{doc_id}').",
                            "tipo": "autogenerada",
                            "run_id": run_id,
                        }

                        nombres_a_id[nombre_limpio] = cluster_id
                        mapa_normalizado_id[nombre_norm] = cluster_id
                        lista_nombres_categorias.append(nombre_limpio)

                        logger.info("NUEVA CATEGORÍA CREADA: '%s' -> %s (doc '%s')", nombre_limpio, cluster_id, doc_id)

                    if cluster_id not in clusters_vistos:
                        clusters_vistos.add(cluster_id)
                        clasificaciones.append({
                            "cluster_id": cluster_id,
                            "categoria": nombre_limpio,
                            "confianza": confianza,
                        })

                etiqueta = {
                    "run_id": run_id,
                    "taxonomia_run_id": info_taxonomia.get("run_id", "unknown"),
                    "modelo_llm": settings.DEEPSEEK_MODEL,
                    "tipo_documento": tipo_normalizado,
                    "clasificaciones": clasificaciones,
                    "revisar_manual": len(clasificaciones) == 0,
                }

                doc_actualizado = dict(item["doc_original"])
                doc_actualizado["clasificacion_llm"] = etiqueta
                resultado_actual.append(doc_actualizado)

            logger.info("Lote %d procesado completamente: %d documentos", idx_lote, len(lote))

        # Guardado único al final del tipo de documento (sin backups, sobreescribe directo)
        storage.guardar_json_atomico(path_salida, resultado_actual)
        logger.info("Clasificación terminada para tipo=%s | salida=%s | documentos=%d", tipo_normalizado, path_salida.name, len(resultado_actual))

    # 4. Guardar taxonomía actualizada con las categorías nuevas
    path_taxonomia = settings.FILE_TAXONOMIA_DESCUBIERTA
    path_taxonomia.parent.mkdir(parents=True, exist_ok=True)
    path_taxonomia.write_text(json.dumps(info_taxonomia, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Taxonomía actualizada guardada en %s", settings.FILE_TAXONOMIA_DESCUBIERTA)

    logger.info("Etapa 2 finalizada correctamente. run_id=%s", run_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ejecutar_clasificacion()