"""Orquestador del pipeline de limpieza y normalización a Markdown (Etapa 0).
Convierte PDF/DOCX/TXT/XLSX a Markdown limpio + secciones con trazabilidad
[linea_inicio, linea_fin], listos para Etapa 1 (extracción)."""
from __future__ import annotations

import gc
import json
import logging
import re
from pathlib import Path

from settings import settings

from .docx_processor import extraer_lineas_docx
from .estructura import DetectorJerarquia, detectar_tipo_documento
from .excel_processor import extraer_lineas_excel
from .gramatical import ReconstructorGramatical
from .metadata import MetadataDocumento
from .modelos import DocumentoLimpio, LineaFuente
from .pdf_processor import extraer_lineas_pdf
from .ruido import detectar_lineas_repetidas, eliminar_ruido, separar_indice_y_bibliografia
from .txt_processor import extraer_lineas_txt

logger = logging.getLogger("clean.pipeline")

EXTENSIONES_SOPORTADAS = {".pdf", ".docx", ".txt", ".xlsx", ".xls"}

# Dominios/expresiones que NUNCA se descartan como "ruido repetido" en leyes
# chilenas, aunque aparezcan en cada página (son parte del contenido oficial).
PATRONES_PRESERVAR_LEY_CHILE = [
    re.compile(r"(bcn\.cl|leychile\.cl|diariooficial\.cl)", re.I),
    re.compile(r"(D\.O\.?|Diario Oficial)", re.I),
]


def _cargar_cleaning_rules() -> dict:
    ruta_rules = settings.CLEANING_RULES_PATH
    if ruta_rules.exists():
        with open(ruta_rules, "r", encoding="utf-8") as f:
            return json.load(f)
    logger.warning("No se encontró el archivo de reglas en: %s", ruta_rules)
    return {}


CLEANING_RULES = _cargar_cleaning_rules()

# El reconstructor gramatical carga spaCy una sola vez y se reutiliza en
# todos los archivos — instanciarlo por documento sería recargar el modelo
# cientos de veces innecesariamente.
_reconstructor = ReconstructorGramatical(
    modelo_spacy="es_core_news_sm",
    preservar_hifen=CLEANING_RULES.get("hyphenation_rules", {}).get("preserve_hyphenated", []),
)


def _extraer_lineas(ruta: Path) -> list[LineaFuente]:
    ext = ruta.suffix.lower()
    if ext == ".pdf":
        return extraer_lineas_pdf(ruta)
    if ext == ".docx":
        return extraer_lineas_docx(ruta)
    if ext == ".txt":
        return extraer_lineas_txt(ruta)
    if ext in (".xlsx", ".xls"):
        return extraer_lineas_excel(ruta)
    raise ValueError(f"Extensión no soportada: {ext}")


def procesar_archivo(ruta_in: Path, ruta_out_md: Path, ruta_out_json: Path, categoria: str) -> bool:
    """Procesa un archivo fuente y escribe dos salidas:
    - ruta_out_md:   Markdown limpio (frontmatter + jerarquía + texto), listo
                      para Etapa 1 — sin comentarios ni redundancias de formato.
    - ruta_out_json: secciones con trazabilidad [linea_inicio, linea_fin]
                      vinculada al archivo de origen, para auditoría/RAG.
    Devuelve False si ya existían ambas salidas (permite resume incremental)."""
    if ruta_out_md.exists() and ruta_out_json.exists():
        return False

    try:
        lineas = _extraer_lineas(ruta_in)
        if not lineas:
            logger.warning("Sin texto extraíble: %s", ruta_in.name)
            return False

        # El tipo de documento se detecta ANTES de limpiar ruido, porque
        # decide qué patrones "preservar" aplicar durante la limpieza
        # (p.ej. dominios oficiales de leyes chilenas).
        muestra_cruda = "\n".join(l.texto for l in lineas[:100])
        tipo_documento = detectar_tipo_documento(muestra_cruda, CLEANING_RULES)

        patrones_preservar = PATRONES_PRESERVAR_LEY_CHILE if tipo_documento == "LEY_CHILE" else []
        lineas_repetidas = detectar_lineas_repetidas(lineas, patrones_preservar=patrones_preservar)
        lineas = eliminar_ruido(lineas, lineas_repetidas)

        patron_entrada_indice = re.compile(
            CLEANING_RULES.get("index_line_patterns", {}).get("linea_indice_simple", r"^$")
        )
        lineas, _indice, _biblio = separar_indice_y_bibliografia(lineas, patron_entrada_indice)

        detector = DetectorJerarquia(CLEANING_RULES, tipo_documento)
        bloques = _reconstructor.reconstruir(lineas, detector.es_linea_estructural)
        secciones = detector.segmentar(bloques)

        metadata = MetadataDocumento.desde_archivo(ruta_in, categoria)
        documento = DocumentoLimpio(
            source_path=metadata.source_path,
            titulo=metadata.titulo,
            categoria=metadata.categoria,
            tipo_documento=tipo_documento,
            processed_date=metadata.processed_date,
            secciones=secciones,
        )

        ruta_out_md.write_text(documento.a_markdown(), encoding="utf-8")
        ruta_out_json.write_text(
            json.dumps(documento.a_dict_trazabilidad(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return True

    except Exception as e:
        logger.error("Error procesando %s: %s", ruta_in.name, e)
        return False


def ejecutar_pipeline() -> None:
    logger.info("🚀 Iniciando pipeline de limpieza (Etapa 0)...")
    tot_proc, tot_omit = 0, 0

    for cfg in settings.RUTAS_CATEGORIAS:
        categoria = cfg["categoria"]
        p_in, p_out = cfg["input_dir"], cfg["output_dir"]

        if not p_in.exists():
            logger.warning("Omite categoría %s: no existe %s", categoria, p_in)
            continue

        p_out.mkdir(parents=True, exist_ok=True)
        archivos = [f for f in p_in.rglob("*") if f.is_file() and f.suffix.lower() in EXTENSIONES_SOPORTADAS]

        proc, omit = 0, 0
        for i, archivo in enumerate(archivos, 1):
            ruta_md = p_out / f"{archivo.stem}.md"
            ruta_json = p_out / f"{archivo.stem}.secciones.json"
            if procesar_archivo(archivo, ruta_md, ruta_json, categoria):
                proc += 1
            else:
                omit += 1
            if i % 10 == 0:
                gc.collect()

        tot_proc += proc
        tot_omit += omit
        logger.info("✔ %s -> Nuevos: %d | Omitidos: %d", categoria, proc, omit)

    logger.info("🎉 Finalizado -> Procesados: %d | Omitidos: %d", tot_proc, tot_omit)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    ejecutar_pipeline()