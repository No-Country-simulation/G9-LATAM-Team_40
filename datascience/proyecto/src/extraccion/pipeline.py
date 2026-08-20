"""Orquestación del pipeline completo, con resumen incremental robusto y parseo híbrido."""
from __future__ import annotations

import gc
import json
import logging
import re
from pathlib import Path

import spacy
import yake
from unstructured.partition.text import partition_text

# ------------------------------------------------------------------------------
# IMPORTACIÓN DE CONFIGURACIÓN CENTRALIZADA
# ------------------------------------------------------------------------------
from settings import settings

# ------------------------------------------------------------------------------
# IMPORTACIONES RELATIVAS DEL MÓDULO DE EXTRACCIÓN (mismo directorio src/extraccion)
# ------------------------------------------------------------------------------
from .extraccion import (
    construir_patrones_dominio,
    extraer_entidades_dominio,
    parsear_markdown_a_secciones,
)
from .llm_client import ExtractorLLM
from .normalizacion import (
    construir_indice_entidades,
    construir_mapa_lemas,
    normalizar_key,
    normalizar_key_lemma,
    normalizar_texto,
)
from .reglas import cargar_reglas
from .relaciones import (
    enriquecer_relaciones,
    extraer_relaciones_spacy,
    merge_entidades,
    merge_relaciones,
    seccion_es_relevante,
)

logger = logging.getLogger(__name__)


def _cargar_documentos_procesados(out_file: Path) -> dict:
    if not out_file.exists():
        return {}
    try:
        with open(out_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {doc["documento_nombre"]: doc for doc in data}
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("No se pudo leer el JSON previo (%s), se empieza desde cero.", e)
        return {}


def _documento_ya_completo(doc_guardado: dict | None) -> bool:
    """
    Verifica si el documento ya está guardado en el JSON previo.
    Se considera completo si existe y tiene al menos una sección procesada,
    evitando re-procesamientos por metadatos opcionales o conteos variables.
    """
    if not doc_guardado:
        return False
    secciones = doc_guardado.get("secciones", [])
    return len(secciones) > 0


class Pipeline:
    def __init__(self, settings: Settings) -> None:
        settings.ensure_dirs()
        self.settings = settings
        self.reglas = cargar_reglas(
            config_path=settings.CONFIG_RULES_PATH,
            relations_path=settings.RELATIONS_PATH,
            glosario_path=settings.GLOSARIO_PATH
        )

        self.indice_entidades = construir_indice_entidades(self.reglas.diccionario_dominio)
        self.patrones_dominio = construir_patrones_dominio(self.reglas.diccionario_dominio)

        self.nlp = spacy.load(settings.SPACY_MODEL)
        ruler = self.nlp.add_pipe("entity_ruler", before="parser")
        ruler.add_patterns([
            {"label": "ROL_LEGAL", "pattern": [{"LOWER": palabra.lower()} for palabra in rol.split()]}
            for rol in self.reglas.roles_legales
        ])

        self.kw_extractor = yake.KeywordExtractor(lan="es", n=3, dedupLim=0.8, top=20)

        # Precompilación de expresiones regulares para el glosario
        self._patron_glosario = None
        if self.reglas.glosario:
            terminos_ordenados = sorted(self.reglas.glosario.keys(), key=len, reverse=True)
            self._patron_glosario = re.compile(
                r"\b(" + "|".join(re.escape(k) for k in terminos_ordenados) + r")\b",
                re.IGNORECASE
            )

        self.llm = ExtractorLLM(
            gemini_api_key=settings.GEMINI_API_KEY,
            gemini_models=[settings.GEMINI_MODEL_1, settings.GEMINI_MODEL_2],
            deepseek_api_key=settings.DEEPSEEK_API_KEY,
            deepseek_model=settings.DEEPSEEK_MODEL,
            deepseek_base_url=settings.DEEPSEEK_BASE_URL,
            prompt_path=settings.PROMPT_EXTRACTION_PATH,
            max_retries=settings.GEMINI_MAX_RETRIES,
            rate_limit_seconds=settings.GEMINI_RATE_LIMIT_SECONDS,
        )

    def _tipo_documento(self, archivo: Path):
        if "ISOS" in archivo.parts:
            return "ISO"
        if "LEYES" in archivo.parts:
            return "LEY"
        return "DESCONOCIDO"

    def _procesar_seccion(self, seccion: dict, doc) -> dict:
        texto = seccion["texto"]

        entidades_dominio = extraer_entidades_dominio(
            texto,
            self.indice_entidades,
            self.patrones_dominio
        )

        for ent in doc.ents:
            if ent.label_ == "ROL_LEGAL":
                entidades_dominio.append({
                    "texto": ent.text,
                    "texto_normalizado": normalizar_texto(ent.text),
                    "canonical": ent.text.upper(),
                    "tipo": "ROL_LEGAL",
                    "origen": "spacy_entity_ruler",
                })

        mapa_lemas = construir_mapa_lemas(doc)
        entidades_dominio = list({
            (normalizar_key_lemma(e["texto"], mapa_lemas), e["tipo"]): e
            for e in entidades_dominio
        }.values())

        relaciones_spacy = enriquecer_relaciones(
            extraer_relaciones_spacy(doc, self.reglas.mapa_relaciones), entidades_dominio
        )

        conceptos = [
            {"concepto": kw, "score": round(1 / (1 + score), 3)}
            for kw, score in self.kw_extractor.extract_keywords(texto)
            if len(kw) > 3 and kw.lower() not in self.reglas.stopwords_custom
        ]

        entidades_final, relaciones_final = list(entidades_dominio), list(relaciones_spacy)
        llamo_llm = seccion_es_relevante(texto, entidades_dominio, self.reglas.mapa_relaciones, conceptos)
        modelo_llm_usado = None

        if llamo_llm:
            glosario_relevante = {}
            if self._patron_glosario:
                coincidencias = set(self._patron_glosario.findall(texto))
                for match in coincidencias:
                    match_lower = match.lower()
                    for termino, info in self.reglas.glosario.items():
                        if termino.lower() == match_lower:
                            glosario_relevante[termino] = {
                                "termino": info.get("termino", termino),
                                "definicion": info.get("definicion", "")
                            }

            data_llm = self.llm.analizar_seccion(
                texto,
                entidades_dominio,
                glosario_relevante
            )

            entidades_final = merge_entidades(data_llm.get("entidades", []), entidades_dominio, texto)
            relaciones_final = merge_relaciones(data_llm.get("relaciones", []), relaciones_spacy)
            modelo_llm_usado = data_llm.get("modelo_usado")

        return {
            "titulo": seccion["titulo"],
            "nivel": seccion["nivel"],
            "ruta_jerarquica": seccion["ruta_jerarquica"],
            "texto": texto,
            "entidades": entidades_final,
            "conceptos": conceptos,
            "relaciones": relaciones_final,
            "llm_consultado": llamo_llm,
            "modelo_llm_usado": modelo_llm_usado,
        }

    def _procesar_documento(self, archivo: Path, documento_parsed: dict | None = None) -> dict | None:
        if documento_parsed is None:
            documento_parsed = parsear_markdown_a_secciones(archivo)

        secciones = documento_parsed.get("secciones", [])
        metadata = documento_parsed.get("metadata", {"indice": [], "bibliografia": []})

        if not secciones:
            return None

        registros = []
        docs = self.nlp.pipe([s["texto"] for s in secciones], batch_size=4)

        for s_idx, (seccion, doc) in enumerate(zip(secciones, docs), 1):
            registro = self._procesar_seccion(seccion, doc)
            registros.append(registro)
            logger.info(
                "    └─ Sec %d/%d (%s): %d ent | %d rel",
                s_idx,
                len(secciones),
                "LLM" if registro["llm_consultado"] else "solo-reglas",
                len(registro["entidades"]),
                len(registro["relaciones"]),
            )

        return {
            "documento_id": archivo.stem,
            "documento_nombre": archivo.name,
            "metadata": metadata,
            "secciones": registros,
        }

    def ejecutar(self) -> None:
        grupos = []
        for cat_info in self.settings.RUTAS_CATEGORIAS:
            categoria = cat_info["categoria"]
            output_dir = cat_info["output_dir"]

            if categoria == "ISOS":
                archivo_salida = self.settings.FILE_ISO_EXTRACCION

            elif categoria == "LEYES":
                archivo_salida = self.settings.FILE_LEYES_EXTRACCION
            else:
                continue

            archivos_md = sorted(output_dir.rglob("*.md")) if output_dir.exists() else []
            grupos.append((categoria, archivos_md, archivo_salida))
            logger.info("Grupo:", grupos)

        totales_archivos = sum(len(archivos) for _, archivos, _ in grupos)
        logger.info("Documentos encontrados: %d", totales_archivos)

        idx_global = 1
        for tipo, archivos, output in grupos:
            if not archivos:
                continue

            documentos_previos = _cargar_documentos_procesados(output)
            documentos_finales = dict(documentos_previos)

            logger.info("Documentos previos %s: %d", tipo, len(documentos_previos))
            output.parent.mkdir(parents=True, exist_ok=True)

            for archivo in archivos:
                self.tipo_documento = tipo
                try:
                    # 1. Comprobación anticipada: si el documento ya está en el JSON, se omite
                    doc_previo = documentos_previos.get(archivo.name)

                    if _documento_ya_completo(doc_previo):
                        logger.info(
                            "[%d/%d] ✅ %s ya procesado (omitido)",
                            idx_global,
                            totales_archivos,
                            archivo.name
                        )
                        continue

                    # 2. Parseo y procesamiento únicamente si el documento no existe o falta
                    documento_parsed = parsear_markdown_a_secciones(archivo)
                    secciones = documento_parsed.get("secciones", [])

                    if not secciones:
                        logger.info(
                            "[%d/%d] ⏭️ %s sin secciones válidas",
                            idx_global,
                            totales_archivos,
                            archivo.name
                        )
                        continue

                    if doc_previo is not None:
                        logger.info("🔄 %s incompleto — se reprocesa.", archivo.name)

                    resultado = self._procesar_documento(archivo, documento_parsed=documento_parsed)

                    if resultado is None:
                        continue

                    documentos_finales[archivo.name] = resultado

                    output.write_text(
                        json.dumps(
                            list(documentos_finales.values()),
                            ensure_ascii=False,
                            indent=2
                        ),
                        encoding="utf-8"
                    )

                    logger.info(
                        "[%d/%d] 💾 %s guardado en %s",
                        idx_global,
                        totales_archivos,
                        archivo.name,
                        tipo
                    )
                except Exception as e:
                    logger.error(
                        "[%d/%d] ❌ Error procesando %s: %s",
                        idx_global,
                        totales_archivos,
                        archivo.name,
                        e
                    )
                finally:
                    idx_global += 1
                    gc.collect()

        logger.info("🎉 Proceso terminado exitosamente.")
        logger.info("ISOS: %s", self.settings.FILE_ISO_EXTRACCION.resolve())
        logger.info("LEYES: %s", self.settings.FILE_LEYES_EXTRACCION.resolve())