"""Etapa 1: Descubrimiento de Taxonomía (Ejecución Offline / Local)."""

import json
import logging
import re
import unicodedata
from datetime import datetime
from string import Template
from openai import OpenAI
from pydantic import ValidationError

from settings import settings
from schemas import TaxonomiaDescubierta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Descubrimiento_Taxonomia")


def cargar_titulos() -> list[dict]:
    documentos = []
    for tipo, ruta in settings.INPUT_FILES.items():
        if not ruta.exists():
            logger.warning("No existe: %s — se omite '%s'.", ruta, tipo)
            continue

        lista_docs = json.loads(ruta.read_text(encoding="utf-8"))
        logger.info("Cargando %s: %d documentos", tipo, len(lista_docs))

        for idx, doc in enumerate(lista_docs):
            identificador = (
                doc.get("documento_id")
                or doc.get("metadata", {}).get("archivo")
                or f"{tipo}_{idx}"
            )
            titulo = doc.get("documento_nombre") or identificador
            titulos_secciones = [
                sec.get("titulo", "").strip()
                for sec in doc.get("secciones", [])
                if sec.get("titulo", "").strip()
            ]
            documentos.append(
                {
                    "documento_id": identificador,
                    "tipo_documento": tipo,
                    "titulo_documento": titulo,
                    "titulos_secciones": titulos_secciones,
                }
            )
    return documentos


def generar_slug(nombre: str, slugs_usados: set[str]) -> str:
    sin_acentos = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9]+", "_", sin_acentos).strip("_").upper()[:60]
    slug_final = slug
    contador = 2
    while slug_final in slugs_usados:
        slug_final = f"{slug}_{contador}"
        contador += 1
    slugs_usados.add(slug_final)
    return slug_final


def descubrir_taxonomia(documentos: list[dict], reintentos: int = 2) -> list[dict]:
    settings.validate_keys()
    client = OpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )

    resumen_titulos = [
        {
            "documento_id": d["documento_id"],
            "titulo": d["titulo_documento"],
            "secciones": d["titulos_secciones"][:15],
        }
        for d in documentos
    ]

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
            res = client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = res.choices[0].message.content or ""
            raw = re.sub(r"^```json\s*|\s*```$", "", content.strip())
            taxonomia = TaxonomiaDescubierta.model_validate_json(raw)

            if len(taxonomia.categorias) < settings.MIN_CATEGORIAS:
                logger.warning(
                    "El LLM propuso %d categorías (mínimo %d). Reintentando...",
                    len(taxonomia.categorias),
                    settings.MIN_CATEGORIAS,
                )
                if intento < reintentos:
                    continue

            return [c.model_dump() for c in taxonomia.categorias]

        except (ValidationError, json.JSONDecodeError, Exception) as e:
            logger.warning("Error en intento %d/%d: %s", intento + 1, reintentos + 1, e)
            if intento == reintentos:
                raise RuntimeError(
                    f"No se pudo generar taxonomía tras {reintentos + 1} intentos: {e}"
                )

    raise RuntimeError("No se pudo generar la taxonomía.")


def ejecutar_descubrimiento() -> None:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("Iniciando Descubrimiento de Taxonomía (run_id: %s)", run_id)

    documentos = cargar_titulos()
    if not documentos:
        logger.error("No se encontraron documentos de entrada. Proceso abortado.")
        return

    logger.info("Total documentos analizados: %d", len(documentos))
    categorias = descubrir_taxonomia(documentos)

    slugs_usados: set[str] = set()
    categorias_con_id = {}
    for c in categorias:
        categoria_id = generar_slug(c["nombre"], slugs_usados)
        categorias_con_id[categoria_id] = {
            "nombre": c["nombre"],
            "descripcion": c["descripcion"],
        }

    settings.FILE_TAXONOMIA_DESCUBIERTA.parent.mkdir(parents=True, exist_ok=True)
    contenido_salida = {
        "run_id": run_id,
        "fecha": datetime.now().isoformat(),
        "total_categorias": len(categorias_con_id),
        "categorias": categorias_con_id,
    }

    settings.FILE_TAXONOMIA_DESCUBIERTA.write_text(
        json.dumps(contenido_salida, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info(
        "Taxonomía generada con éxito (%d categorías). Guardada en: %s",
        len(categorias_con_id),
        settings.FILE_TAXONOMIA_DESCUBIERTA.resolve(),
    )


if __name__ == "__main__":
    ejecutar_descubrimiento()