"""Cliente LLM (DeepSeek y Gemini): esquema de salida estructurada, llamada con
reintentos, y rotación "pegajosa" (sticky) entre modelos cuando hay cuota
agotada o problemas de conexión.
"""
from __future__ import annotations

import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from openai import OpenAI
from google import genai  # SDK nuevo (pip install google-genai)
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class EntidadLLM(BaseModel):
    texto: str = Field(description="Nombre o texto exacto de la entidad o concepto.")
    tipo: str = Field(
        description="Categoría: ROL_LEGAL, NORMA, MEDIDA_TECNICA, CONCEPTO_CLAVE, EQUIPO, "
        "RIESGO, ENTIDAD_ORGANIZACIONAL, VALOR_PARAMETRO."
    )


class TripletaLLM(BaseModel):
    sujeto: str = Field(description="Entidad/concepto explicito ejecutor de la accion. PROHIBIDO PRONOMBRES.")
    relacion: str = Field(description="Verbo de relación normalizado en MAYÚSCULAS y SNAKE_CASE.")
    objeto: str = Field(description="Entidad/concepto objetivo. PROHIBIDO PRONOMBRES.")
    tipo_relacion: str = Field(description="Categoría: LEGAL, TECNICA, OPERATIVA, ESTRUCTURAL, CONDICIONAL.")
    contexto: str = Field(description="Cita o frase textual exacta de donde proviene esta relacion.")


class AnalisisSeccionLLM(BaseModel):
    entidades: list[EntidadLLM] = Field(default_factory=list)
    relaciones: list[TripletaLLM] = Field(default_factory=list)
    glosario_relevante: dict[str, str] = Field(default_factory=dict, description="Términos del glosario detectados en la sección y sus definiciones.")


JSON_SCHEMA_STR = json.dumps(AnalisisSeccionLLM.model_json_schema(), ensure_ascii=False, indent=2)


# Palabras clave para detectar errores "temporales" (cuota/conexión) que
# justifican rotar de modelo, tanto para Gemini como para DeepSeek.
_PALABRAS_ERROR_TEMPORAL = (
    "quota", "limit", "429", "resource exhausted", "rate limit",
    "timeout", "timed out", "connection", "network", "unavailable",
    "503", "502", "500", "overloaded", "temporarily",
)


def _es_error_temporal(excepcion: Exception) -> bool:
    texto = str(excepcion).lower()
    return any(palabra in texto for palabra in _PALABRAS_ERROR_TEMPORAL)


class ExtractorLLM:
    def __init__(
        self,
        gemini_api_key: str,
        gemini_models: List[str],
        deepseek_api_key: str,
        deepseek_model: str,
        deepseek_base_url: str,
        prompt_path: Path,
        max_retries: int = 2,
        rate_limit_seconds: float = 4.0,
    ) -> None:

        self._gemini_client = genai.Client(api_key=gemini_api_key)
        self._deepseek_client = OpenAI(api_key=deepseek_api_key, base_url=deepseek_base_url)

        # ------------------------------------------------------------------
        # POOL UNIFICADO de modelos, en el orden de preferencia deseado.
        # Gemini primero (gratuitos), DeepSeek al final como último recurso.
        # Cada entrada es un dict con lo necesario para invocarlo.
        # ------------------------------------------------------------------
        self._pool: List[Dict[str, str]] = (
            [{"proveedor": "gemini", "modelo": m} for m in gemini_models]
            + [{"proveedor": "deepseek", "modelo": deepseek_model}]
        )

        if not self._pool:
            raise ValueError("El pool de modelos está vacío (revisa gemini_models/deepseek_model).")

        # Cursor persistente: índice del modelo "activo" en self._pool.
        # Se mantiene entre llamadas (sticky) — no se resetea a 0 en cada
        # invocación, solo avanza cuando el modelo activo falla.
        self._active_idx: int = 0

        # Prompt
        self._prompt_template = prompt_path.read_text(encoding="utf-8")

        self._max_retries = max_retries
        self.rate_limit_seconds = rate_limit_seconds
        self._last_call_time = 0.0

    # ----------------------------------------------------------------------
    @property
    def modelo_activo(self) -> str:
        entry = self._pool[self._active_idx]
        return f"{entry['proveedor']}:{entry['modelo']}"

    def _enforce_rate_limit(self) -> None:
        """Asegura que pasen al menos 'rate_limit_seconds' entre peticiones."""
        elapsed = time.time() - self._last_call_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)
        self._last_call_time = time.time()

    # ----------------------------------------------------------------------
    def _invocar_gemini(self, modelo: str, prompt: str) -> str:
        response = self._gemini_client.models.generate_content(model=modelo, contents=prompt)
        if not response.text:
            raise RuntimeError(f"Respuesta vacía de Gemini ({modelo})")
        return response.text

    def _invocar_deepseek(self, modelo: str, prompt: str) -> str:
        response = self._deepseek_client.chat.completions.create(
            model=modelo,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        if not response.choices or not response.choices[0].message.content:
            raise RuntimeError(f"Respuesta inválida o vacía de DeepSeek ({modelo})")
        return response.choices[0].message.content

    def _invocar(self, entry: Dict[str, str], prompt: str) -> str:
        if entry["proveedor"] == "gemini":
            return self._invocar_gemini(entry["modelo"], prompt)
        elif entry["proveedor"] == "deepseek":
            return self._invocar_deepseek(entry["modelo"], prompt)
        raise ValueError(f"Proveedor desconocido: {entry['proveedor']}")

    # ----------------------------------------------------------------------
    def _llm_call(self, prompt: str) -> str:
        self._enforce_rate_limit()

        n = len(self._pool)
        ultimo_error: Optional[Exception] = None

        # Intentamos recorrer el pool una vez por cada llamada
        for paso in range(n):
            idx = (self._active_idx + paso) % n
            entry = self._pool[idx]

            try:
                logger.info("Intentando con: %s:%s", entry['proveedor'], entry['modelo'])
                texto = self._invocar(entry, prompt)
                
                # ÉXITO: Mantenemos este modelo como el principal para futuras llamadas
                self._active_idx = idx
                return texto

            except Exception as e:
                ultimo_error = e
                logger.warning("Fallo en %s:%s - Error: %s", entry['proveedor'], entry['modelo'], e)
                
                # AQUÍ LA LÓGICA DE ROTACIÓN:
                # Si falló, movemos el cursor al siguiente para que la próxima 
                # llamada (o el siguiente paso del loop) use el siguiente.
                self._active_idx = (idx + 1) % n
                
                # Si es un error temporal (cuota), el loop continúa automáticamente 
                # al siguiente modelo (paso siguiente).
                continue

        # Si llegamos aquí, todos los modelos fallaron en esta vuelta
        raise RuntimeError(f"Todos los modelos agotados. Último error: {ultimo_error}")
    
    # ----------------------------------------------------------------------
    def analizar_seccion(
        self,
        texto_seccion: str,
        entidades_dominio: List[Dict[str, Any]],
        glosario_relevante: Dict[str, str] = None
    ) -> Dict[str, Any]:

        entidades_hint = ", ".join(
            sorted({e["canonical"] for e in entidades_dominio})
        ) or "(ninguna detectada por reglas)"

        prompt = self._prompt_template.format(
            entidades_hint=entidades_hint,
            json_schema=JSON_SCHEMA_STR,
            texto_seccion=texto_seccion,
        )

        for intento in range(self._max_retries + 1):
            try:
                raw_text = self._llm_call(prompt)

                raw_text = raw_text.strip()
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("\n", 1)[-1]
                if raw_text.endswith("```"):
                    raw_text = raw_text.rsplit("```", 1)[0]
                raw_text = raw_text.strip()

                return AnalisisSeccionLLM.model_validate_json(raw_text).model_dump()

            except (ValidationError, json.JSONDecodeError) as e:
                if intento < self._max_retries:
                    logger.warning("JSON inválido (Intento %s/%s). Reintentando...", intento + 1, self._max_retries)
                    time.sleep(2)
                    continue
                logger.error("Fallo final de validación JSON tras %s reintentos: %s", self._max_retries, e)
                return {"entidades": [], "relaciones": [], "glosario_relevante": {}, "error": str(e)}

            except RuntimeError as e:
                # Todos los modelos del pool fallaron en este intento de _llm_call.
                if intento < self._max_retries:
                    logger.warning(
                        "Todo el pool de modelos falló (Intento %s/%s). Reintentando desde el modelo activo (%s)...",
                        intento + 1, self._max_retries, self.modelo_activo,
                    )
                    time.sleep(2)
                    continue
                logger.error("Fallo crítico: todos los modelos fallaron tras %s reintentos: %s", self._max_retries, e)
                return {"entidades": [], "relaciones": [], "glosario_relevante": {}, "error": str(e)}

            except Exception as e:
                logger.error("Error crítico procesando la sección: %s", e)
                return {"entidades": [], "relaciones": [], "glosario_relevante": {}, "error": str(e)}