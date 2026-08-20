"""
Etapa 1: Descubrimiento de Taxonomía.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import datetime
from string import Template

from openai import OpenAI
from pydantic import ValidationError

from schemas.documento_clasificado import TaxonomiaDescubierta
from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Descubrimiento_Taxonomia")


def normalizar_nombre_categoria(nombre: str) -> str:
    texto = unicodedata.normalize("NFD", str(nombre).strip().lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto)


def cargar_titulos() -> list[dict]:
    documentos = []
    for tipo, ruta in [
        ("LEYES", settings.FILE_LEYES_EXTRACCION),
        ("ISO", settings.FILE_ISO_EXTRACCION),
    ]:
        if not ruta.exists(): 
            logger.warning(
                "No existe: %s — se omite '%s'.",
                ruta,
                tipo
            )
            continue

        lista_docs = json.loads(ruta.read_text(encoding="utf-8"))
        logger.info("Cargando %s: %d documentos", tipo, len(lista_docs))

        for idx, doc in enumerate(lista_docs):
            identificador = doc.get("documento_id") or doc.get("metadata", {}).get("archivo") or f"{tipo}_{idx}"
            titulo = doc.get("documento_nombre") or identificador
            
            titulos_secciones = [
                sec.get("titulo", "").strip()
                for sec in doc.get("secciones", [])
                if isinstance(sec, dict) and sec.get("titulo", "").strip()
            ]

            relaciones = doc.get("relaciones", [])

            documentos.append({
                "documento_id": identificador,
                "tipo_documento": tipo,
                "titulo_documento": titulo,
                "titulos_secciones": titulos_secciones,
                "relaciones": relaciones,
            })
    return documentos


def generar_slug(nombre: str, slugs_usados: set[str]) -> str:
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9]+", "_", sin_acentos).strip("_").upper()[:60]
    
    slug_final, contador = slug, 2
    while slug_final in slugs_usados:
        slug_final = f"{slug}_{contador}"
        contador += 1

    slugs_usados.add(slug_final)
    return slug_final


def descubrir_taxonomia(documentos: list[dict], reintentos: int = 2) -> list[dict]:
    settings.validate_keys()
    client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=settings.DEEPSEEK_BASE_URL)

    # AJUSTE 1: Incluimos las relaciones en el resumen enviado al LLM
    resumen_titulos = [
        {
            "documento_id": d["documento_id"], 
            "tipo_documento": d["tipo_documento"], 
            "titulo": d["titulo_documento"], 
            "secciones": d["titulos_secciones"],
            "relaciones": d["relaciones"] # <--- Ahora el LLM puede descubrir categorías basadas en relaciones
        }
        for d in documentos
    ]
    logger.info("Enviando al LLM datos de %d documentos (incluyendo relaciones).", len(resumen_titulos))

    prompt_path = settings.PROMPTS_DIR / "prompt_descubrimiento.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"No existe el archivo de prompt en: {prompt_path}")

    prompt = Template(prompt_path.read_text(encoding="utf-8")).substitute(
        total_documentos=len(documentos),
        min_categorias=settings.MIN_CATEGORIAS,
        resumen_titulos=json.dumps(resumen_titulos, ensure_ascii=False, indent=2),
        json_schema=json.dumps(TaxonomiaDescubierta.model_json_schema(), ensure_ascii=False),
    )
    for intento in range(reintentos + 1):
            try:
                logger.info("Intento de descubrimiento %d/%d", intento + 1, reintentos + 1)
                res = client.chat.completions.create(
                    model=settings.DEEPSEEK_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )

                content = res.choices[0].message.content or ""
                raw = re.sub(r"^```json\s*|\s*```$", "", content.strip())
                taxonomia = TaxonomiaDescubierta.model_validate_json(raw)

                # Validar mínimo de categorías
                if len(taxonomia.categorias) < settings.MIN_CATEGORIAS:
                    logger.warning("El LLM propuso %d categorías. Mínimo esperado: %d.", len(taxonomia.categorias), settings.MIN_CATEGORIAS)
                    if intento < reintentos:
                        continue

                return [cat.model_dump() for cat in taxonomia.categorias]

            except (ValidationError, json.JSONDecodeError, Exception) as e:
                logger.warning("Error en intento %d/%d: %s", intento + 1, reintentos + 1, e)
                if intento == reintentos:
                    raise RuntimeError(f"No se pudo generar la taxonomía tras {reintentos + 1} intentos: {e}")

    raise RuntimeError("No se pudo generar la taxonomía.")


def ejecutar_descubrimiento() -> None:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("Iniciando Descubrimiento de Taxonomía (run_id: %s)", run_id)

    documentos = cargar_titulos()
    if not documentos:
        logger.error("No se encontraron documentos.")
        return
    logger.info("Total documentos analizados: %d", len(documentos))

    categorias = descubrir_taxonomia(documentos)

    slugs_usados, categorias_con_id, nombres_normalizados = set(), {}, {}

    for categoria in categorias:
        nombre = categoria["nombre"].strip()
        nombre_norm = normalizar_nombre_categoria(nombre)
        if not nombre_norm:
            continue

        if nombre_norm in nombres_normalizados:
            logger.warning("Categoría duplicada descartada: '%s'. Equivalente a '%s'.", nombre, nombres_normalizados[nombre_norm])
            continue

        categoria_id = generar_slug(nombre, slugs_usados)
        categorias_con_id[categoria_id] = {"nombre": nombre, "descripcion": categoria["descripcion"]}
        nombres_normalizados[nombre_norm] = nombre

    settings.FILE_TAXONOMIA_DESCUBIERTA.parent.mkdir(parents=True, exist_ok=True)
    
    contenido_salida = {
        "run_id": run_id,
        "fecha": datetime.now().isoformat(),
        "total_categorias": len(categorias_con_id),
        "categorias": categorias_con_id,
    }

    path_temporal = settings.FILE_TAXONOMIA_DESCUBIERTA.with_suffix(".tmp")
    path_temporal.write_text(json.dumps(contenido_salida, ensure_ascii=False, indent=2), encoding="utf-8")
    path_temporal.replace(settings.FILE_TAXONOMIA_DESCUBIERTA)

    logger.info("Taxonomía generada correctamente. %d categorías.", len(categorias_con_id))
    logger.info("Archivo: %s", settings.FILE_TAXONOMIA_DESCUBIERTA.resolve())


if __name__ == "__main__":
    ejecutar_descubrimiento()