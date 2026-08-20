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

    # 0. Verificación automática: Si no existe la taxonomía, ejecutar Etapa 1 primero
    path_taxonomia = settings.FILE_TAXONOMIA_DESCUBIERTA
    if not path_taxonomia.exists():
        logger.info("No se encontró el archivo de taxonomía en %s.", path_taxonomia)
        logger.info("Iniciando automáticamente la Etapa 1 (Descubrimiento de Taxonomía)...")
        try:
            # Importa y ejecuta la función principal de la Etapa 1
            from .descubrimiento_taxonomia import ejecutar_descubrimiento
            ejecutar_descubrimiento()
            logger.info("Etapa 1 completada con éxito. Continuando con la clasificación...")
        except Exception as e:
            raise RuntimeError(
                f"No se pudo generar la taxonomía automáticamente en la Etapa 1: {e}"
            ) from e

    logger.info("Iniciando Etapa 2 - Clasificación con Memoria Incremental. run_id=%s", run_id)

    # 1. Cargar taxonomía
    info_taxonomia, nombres_a_id, lista_nombres_categorias = storage.cargar_taxonomia()
    if not lista_nombres_categorias:
        raise RuntimeError("No se encontró ninguna categoría en la taxonomía. Ejecuta primero la Etapa 1.") 
    
    logger.info("Taxonomía cargada: %d categorías", len(lista_nombres_categorias))

    mapa_normalizado_id = {
        normalizar_texto(nombre): cluster_id
        for nombre, cluster_id in nombres_a_id.items()
    }

    # Slugs ya usados en la taxonomía
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

        # Cargar documentos fuente actuales
        lista_docs_fuente = json.loads(ruta.read_text(encoding="utf-8"))
        logger.info("Tipo: %s | Total documentos en fuente: %d", tipo_normalizado, len(lista_docs_fuente))

        # Cargar resultados previos si existen (Memoria / Persistencia)
        documentos_previos_map = {}
        if path_salida.exists():
            try:
                docs_previos = json.loads(path_salida.read_text(encoding="utf-8"))
                for doc_p in docs_previos:
                    # Reconstruir identificador idéntico al generador
                    idx_temp = 0 # fallback match
                    identif_p = (
                        doc_p.get("documento_id")
                        or doc_p.get("metadata", {}).get("archivo")
                    )
                    if identif_p:
                        documentos_previos_map[identif_p] = doc_p
                logger.info("Se recuperaron %d documentos clasificados previamente.", len(documentos_previos_map))
            except Exception as e:
                logger.warning("No se pudo leer el archivo previo en %s: %s", path_salida, e)

        resultado_actual: list[dict] = []
        pendientes = []

        for idx, doc in enumerate(lista_docs_fuente):
            identificador = (
                doc.get("documento_id")
                or doc.get("metadata", {}).get("archivo")
                or f"{tipo_normalizado}_{idx}"
            )

            # Si el documento ya fue clasificado anteriormente, respetamos su clasificación previa
            if identificador in documentos_previos_map:
                logger.debug("Documento ya existente conservado: '%s'", identificador)
                resultado_actual.append(documentos_previos_map[identificador])
                continue

            # Si es nuevo, preparamos sus metadatos basados estrictamente en títulos y nombres
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
                "relaciones": doc.get("relaciones", []), 
            })

        logger.info("Documentos nuevos pendientes de clasificar: %d", len(pendientes))

        if not pendientes:
            logger.info("No hay nuevos documentos para procesar en tipo=%s.", tipo_normalizado)
            storage.guardar_json_atomico(path_salida, resultado_actual)
            continue

        # 3. Procesamiento por lotes solo para documentos NUEVOS
        lote_size = settings.DOCUMENTOS_POR_LOTE
        for idx_lote, i in enumerate(range(0, len(pendientes), lote_size), start=1):
            lote = pendientes[i : i + lote_size]
            logger.info("Procesando lote NUEVO %d: %d documentos", idx_lote, len(lote))

            resultado_lote = classifier.clasificar_lote(lote)
            mapa_resultado = {r.get("documento_id"): r for r in resultado_lote if r.get("documento_id")}

            for item in lote:
                doc_id = item["documento_id"]
                r = mapa_resultado.get(doc_id, {"categorias_asignadas": [], "confianzas": [], "palabras_claves": []})
                categorias = r.get("categorias_asignadas", [])
                confianzas = r.get("confianzas", [])
                lista_palabras = r.get("palabras_claves", [])

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

                    if not (0.0 <= confianza <= 1.0) or confianza < settings.UMBRAL_CONFIANZA:
                        continue

                    nombre_norm = normalizar_texto(nombre_limpio)
                    cluster_id = mapa_normalizado_id.get(nombre_norm)

                    # Si la categoría no encaja en las existentes, se crea una nueva (Dinámica)
                    if cluster_id is None:
                        cluster_id = generar_slug_categoria(nombre_limpio, slugs_usados)
                        info_taxonomia.setdefault("categorias", {})[cluster_id] = {
                            "nombre": nombre_limpio,
                            "descripcion": f"Categoría autogenerada basada en títulos (detectada en '{doc_id}').",
                            "tipo": "autogenerada",
                            "run_id": run_id,
                        }

                        nombres_a_id[nombre_limpio] = cluster_id
                        mapa_normalizado_id[nombre_norm] = cluster_id
                        lista_nombres_categorias.append(nombre_limpio)

                        logger.info("NUEVA CATEGORÍA DINÁMICA CREADA: '%s' -> %s (por doc '%s')", nombre_limpio, cluster_id, doc_id)
                    if cluster_id not in clusters_vistos:
                        clusters_vistos.add(cluster_id)

                        palabras_cat = lista_palabras[posicion] if posicion < len(lista_palabras) else []

                        clasificaciones.append({
                            "cluster_id": cluster_id,
                            "categoria": nombre_limpio,
                            "confianza": confianza,
                            "palabras_claves": palabras_cat
                        })

                etiqueta = {
                    "documento_id": doc_id,
                    "fecha_procesamiento": datetime.now().isoformat(),
                    "run_id": run_id,
                    "taxonomia_run_id": info_taxonomia.get("run_id", "unknown"),
                    "modelo_llm": settings.DEEPSEEK_MODEL,
                    "tipo_documento": tipo_normalizado,
                    "clasificaciones": clasificaciones,
                }

                resultado_actual.append(etiqueta)

        # Guardado incremental actualizado
        storage.guardar_json_atomico(path_salida, resultado_actual)
        logger.info("Clasificación incremental finalizada para tipo=%s | salida=%s | total documentos=%d", 
                    tipo_normalizado, path_salida.name, len(resultado_actual))

    # 4. Guardar taxonomía actualizada en caso de haber descubierto nuevas categorías
    path_taxonomia = settings.FILE_TAXONOMIA_DESCUBIERTA
    path_taxonomia.parent.mkdir(parents=True, exist_ok=True)
    path_taxonomia.write_text(json.dumps(info_taxonomia, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Taxonomía actualizada guardada correctamente.")