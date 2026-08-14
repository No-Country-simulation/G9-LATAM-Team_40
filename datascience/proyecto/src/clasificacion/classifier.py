"""Módulo encargado de interactuar con el LLM para la clasificación por lotes."""

from __future__ import annotations

import json
import logging
import re
from string import Template
from openai import OpenAI
from pydantic import ValidationError

from settings import Settings
from schemas.documento_clasificado import LoteClasificado
logger = logging.getLogger(__name__)


class DocumentClassifier:
    def __init__(self, settings: Settings, categorias_nombres: list[str]):
        self.settings = settings
        self.categorias_nombres = categorias_nombres
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self.prompt_template = self._cargar_prompt_template()

    def _cargar_prompt_template(self) -> Template:
        path = self.settings.PROMPTS_DIR / "prompt_clasificacion.txt"
        if not path.exists():
            raise FileNotFoundError(
                f"No se encontró el prompt de clasificación en: {path.resolve()}"
            )
        return Template(path.read_text(encoding="utf-8"))

    def clasificar_lote(self, lote: list[dict], reintentos: int = 2) -> list[dict]:
        resumen_lote = []
        for d in lote:
            # Compatibilidad segura para extraer título y secciones independientemente de la estructura
            doc_id = d.get("documento_id", "desconocido")
            titulo = d.get("titulo_documento") or d.get("documento_nombre", "Sin título")
            
            # Extraer títulos de secciones de forma segura
            secciones_raw = d.get("secciones", [])
            titulos_secciones = [s.get("titulo", "") for s in secciones_raw if isinstance(s, dict)]
            
            resumen_lote.append({
                "documento_id": doc_id,
                "titulo": titulo,
                "secciones": titulos_secciones[:15],
            })

        prompt = self.prompt_template.substitute(
            lista_categorias=json.dumps(self.categorias_nombres, ensure_ascii=False, indent=2),
            umbral_confianza=self.settings.UMBRAL_CONFIANZA,
            max_categorias=self.settings.MAX_CATEGORIAS_POR_DOCUMENTO,
            resumen_lote=json.dumps(resumen_lote, ensure_ascii=False, indent=2),
            json_schema=json.dumps(LoteClasificado.model_json_schema(), ensure_ascii=False),
        )

        for intento in range(reintentos + 1):
            try:
                res = self.client.chat.completions.create(
                    model=self.settings.DEEPSEEK_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )
                content = res.choices[0].message.content or ""
                raw = re.sub(r"^```json\s*|\s*```$", "", content.strip())
                resultado = LoteClasificado.model_validate_json(raw)
                return [c.model_dump() for c in resultado.clasificaciones]

            except (ValidationError, json.JSONDecodeError, Exception) as e:
                logger.warning(
                    "Intento %d/%d fallido para el lote: %s",
                    intento + 1,
                    reintentos + 1,
                    e,
                )
                if intento == reintentos:
                    logger.error("Lote marcado como no clasificado tras agotar reintentos.")
                    return [
                        {
                            "documento_id": d.get("documento_id", "desconocido"),
                            "categorias_asignadas": [],
                            "confianzas": [],
                        }
                        for d in lote
                    ]
        return []