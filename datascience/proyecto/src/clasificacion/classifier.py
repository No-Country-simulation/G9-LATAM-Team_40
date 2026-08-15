"""
Módulo encargado de interactuar con el LLM
para la clasificación por lotes.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from string import Template

from openai import OpenAI
from pydantic import ValidationError

from schemas.documento_clasificado import LoteClasificado
from settings import Settings

logger = logging.getLogger(__name__)


class DocumentClassifier:

    def __init__(self, settings: Settings, categorias_nombres: list[str]):
        self.settings = settings
        self.categorias_nombres = categorias_nombres
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=120.0,
        )
        self.prompt_template = self._cargar_prompt_template()

    def _cargar_prompt_template(self) -> Template:
        path = self.settings.PROMPTS_DIR / "prompt_clasificacion.txt"
        if not path.exists():
            raise FileNotFoundError(f"Prompt no encontrado en: {path.resolve()}")
        return Template(path.read_text(encoding="utf-8"))

    def _preparar_resumen(self, lote: list[dict]) -> list[dict]:
        resumen = []
        for idx, doc in enumerate(lote):
            titulos_secciones = doc.get("titulos_secciones") or [
                s.get("titulo", "").strip()
                for s in doc.get("secciones", [])
                if isinstance(s, dict) and s.get("titulo", "").strip()
            ]
            resumen.append({
                "posicion": idx,
                "documento_id": doc.get("documento_id", "desconocido"),
                "titulo": doc.get("titulo_documento") or doc.get("documento_nombre") or "Sin título",
                "secciones": titulos_secciones,
            })
        return resumen

    def _validar_respuesta(self, resultado: LoteClasificado, lote: list[dict]) -> list[dict]:
        # Convertir respuesta Pydantic al formato esperado por main.py
        clasificaciones = []
        for c in resultado.clasificaciones:
            doc_dump = c.model_dump()
            
            # Transformar list[CategoriaAsignada] a dos listas separadas
            cat_asignadas = doc_dump.get("categorias_asignadas", [])
            
            # Extraer nombres y confianzas
            nombres_categorias = [cat_obj["categoria"] for cat_obj in cat_asignadas]
            confianzas_valores = [cat_obj["confianza"] for cat_obj in cat_asignadas]
            
            clasificaciones.append({
                "documento_id": doc_dump.get("documento_id"),
                "categorias_asignadas": nombres_categorias,
                "confianzas": confianzas_valores,
            })
        
        if len(clasificaciones) != len(lote):
            raise ValueError(f"Cantidad incorrecta: LLM devolvió {len(clasificaciones)}, esperados {len(lote)}.")

        ids_esperados = [d.get("documento_id") for d in lote]
        ids_recibidos = [c.get("documento_id") for c in clasificaciones]

        if set(ids_esperados) != set(ids_recibidos):
            raise ValueError(f"IDs no coinciden. Faltantes={set(ids_esperados) - set(ids_recibidos)}, Sobrantes={set(ids_recibidos) - set(ids_esperados)}")

        mapa = {c["documento_id"]: c for c in clasificaciones}
        clasificaciones_ordenadas = [mapa[doc_id] for doc_id in ids_esperados]

        categorias_validas = {self._normalizar(cat) for cat in self.categorias_nombres}

        for c in clasificaciones_ordenadas:
            doc_id = c.get("documento_id")
            cats, confs = c.get("categorias_asignadas") or [], c.get("confianzas") or []

            if len(cats) != len(confs):
                raise ValueError(f"Documento {doc_id}: cantidad desigual de categorías y confianzas.")
            if len(cats) > self.settings.MAX_CATEGORIAS_POR_DOCUMENTO:
                raise ValueError(f"Documento {doc_id} supera el máximo de categorías ({self.settings.MAX_CATEGORIAS_POR_DOCUMENTO}).")

            for cat, conf in zip(cats, confs):
                if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
                    raise ValueError(f"Confianza inválida para {cat}: {conf}")
                if self._normalizar(cat) not in categorias_validas:
                    logger.warning("Categoría nueva detectada por el LLM: '%s'", cat)

        logger.info("Validación exitosa: %d documentos con %d categorías en promedio.", 
                   len(clasificaciones_ordenadas),
                   int(sum(len(c.get("categorias_asignadas", [])) for c in clasificaciones_ordenadas) / max(1, len(clasificaciones_ordenadas))))

        return clasificaciones_ordenadas

    @staticmethod
    def _normalizar(texto: str) -> str:
        texto = unicodedata.normalize("NFD", str(texto).strip().lower())
        return "".join(c for c in texto if unicodedata.category(c) != "Mn")

    def clasificar_lote(self, lote: list[dict], reintentos: int = 2) -> list[dict]:
        resumen_lote = self._preparar_resumen(lote)
        
        prompt = self.prompt_template.substitute(
            lista_categorias=json.dumps(self.categorias_nombres, ensure_ascii=False, indent=2),
            umbral_confianza=self.settings.UMBRAL_CONFIANZA,
            max_categorias=self.settings.MAX_CATEGORIAS_POR_DOCUMENTO,
            resumen_lote=json.dumps(resumen_lote, ensure_ascii=False, indent=2),
            json_schema=json.dumps(LoteClasificado.model_json_schema(), ensure_ascii=False, indent=2),
        )

        logger.info("Clasificando lote de %d documentos.", len(lote))
        logger.debug("Resumen enviado al LLM:\n%s", json.dumps(resumen_lote, ensure_ascii=False, indent=2))

        for intento in range(reintentos + 1):
            content = ""
            try:
                logger.info("Clasificando lote: intento %d/%d", intento + 1, reintentos + 1)
                
                response = self.client.chat.completions.create(
                    model=self.settings.DEEPSEEK_MODEL,
                    messages=[
                        {"role": "system", "content": "Eres un clasificador documental estricto. Debes responder exclusivamente con JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                )

                content = response.choices[0].message.content or ""
                logger.info("RESPUESTA RAW DEL LLM:\n%s", content[:10000])

                if not content.strip():
                    raise ValueError("El LLM devolvió una respuesta vacía.")

                raw = re.sub(r"^```json\s*", "", content.strip(), flags=re.IGNORECASE)
                raw = re.sub(r"\s*```$", "", raw)

                resultado = LoteClasificado.model_validate_json(raw)
                clasificaciones = self._validar_respuesta(resultado, lote)

                logger.info("Lote clasificado correctamente: %d documentos.", len(clasificaciones))
                return clasificaciones

            except (ValidationError, json.JSONDecodeError, ValueError) as error:
                logger.warning("Error de validación en intento %d/%d: %s", intento + 1, reintentos + 1, error)
                if content:
                    logger.warning("Respuesta recibida:\n%s", content[:3000])

            except Exception as error:
                logger.warning("Error de API/LLM en intento %d/%d: %s", intento + 1, reintentos + 1, error)
                if content:
                    logger.warning("Contenido recibido antes del error:\n%s", content[:1000])

            if intento == reintentos:
                logger.error("Lote marcado como NO CLASIFICADO después de agotar %d intentos.", reintentos + 1)
                return [{"documento_id": d.get("documento_id", "desconocido"), "categorias_asignadas": [], "confianzas": []} for d in lote]

        return []

    def generar_etiqueta_propia(self, doc: dict) -> str | None:
        """
        Genera una etiqueta propia cuando la clasificación está vacía.
        Usa el LLM para sugerir una categoría única basada en el contenido del documento.
        """
        titulo = doc.get("titulo_documento") or doc.get("documento_nombre") or "Sin título"
        titulos_secciones = doc.get("titulos_secciones", [])[:5]  # Limitar a 5 secciones
        
        prompt_etiqueta = f"""
Analiza el siguiente documento y sugiere UNA ÚNICA categoría o etiqueta que lo describa mejor.

Título del documento: {titulo}

Secciones principales:
{json.dumps(titulos_secciones, ensure_ascii=False, indent=2)}

Responde SOLO con una categoría en formato JSON simple:
{{"etiqueta": "CATEGORÍA_SUGERIDA"}}

La categoría debe ser:
- Específica y descriptiva
- Una o dos palabras máximo
- Relacionada con el contenido
- Única y original
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Eres un experto en clasificación. Responde solo con JSON."},
                    {"role": "user", "content": prompt_etiqueta}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            
            content = response.choices[0].message.content or "{}"
            raw = re.sub(r"^```json\s*", "", content.strip(), flags=re.IGNORECASE)
            raw = re.sub(r"\s*```$", "", raw)
            
            resultado = json.loads(raw)
            etiqueta = resultado.get("etiqueta", "").strip()
            
            if etiqueta:
                logger.info("Etiqueta propia generada para '%s': %s", doc.get("documento_id"), etiqueta)
                return etiqueta
            
        except Exception as e:
            logger.warning("Error al generar etiqueta propia: %s", e)
        
        return None