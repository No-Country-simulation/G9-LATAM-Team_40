"""
Script principal (Orquestador) de Retrieval y Generación Aumentada (RAG) basado en el Grafo Global.
Etapa 4: reutiliza los nodos, apariciones y relaciones ya construidos en la Etapa 3.
No re-embebe secciones ni re-filtra archivos crudos por consulta.
"""
from __future__ import annotations

import json
import logging
import sys
import textwrap
import time
from typing import List, Dict, Any

import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from settings import settings
from .indice_grafo import IndiceGrafo  # Importación directa asumiendo que están en la misma carpeta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("MAIN_Etapa_4")


class PipelineGraphRAG:
    def __init__(self):
        logger.info("Cargando índice del grafo, embeddings y contenido fuente...")
        self.indice = IndiceGrafo()

        logger.info("Cargando modelo de embeddings '%s'...", settings.MODELO_EMBEDDINGS)
        self.modelo_emb = SentenceTransformer(settings.MODELO_EMBEDDINGS)

        self.client_llm = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )

        self.prompt_sistema = self._cargar_prompt_sistema()

    # --------------------------------------------------------------------
    # Carga del prompt de sistema (una sola vez, no por consulta)
    # --------------------------------------------------------------------
    @staticmethod
    def _cargar_prompt_sistema() -> str:
        """Carga el prompt de sistema una sola vez al iniciar el pipeline.
        Si el archivo falta o está vacío, usa un fallback interno en vez de tumbar el servicio."""
        ruta = settings.PROMPT_RAG_SISTEMA_PATH
        fallback = (
            "Eres un consultor experto en normativas legales e ISO. "
            "Responde basándote ÚNICAMENTE en el contexto proporcionado."
        )
        try:
            texto = ruta.read_text(encoding="utf-8").strip()
            if texto:
                logger.info("Prompt de sistema cargado desde: %s", ruta)
                return texto
            logger.warning("El archivo de prompt está vacío (%s). Usando fallback interno.", ruta)
        except FileNotFoundError:
            logger.warning("No se encontró el prompt en %s. Usando fallback interno.", ruta)
        except Exception as e:
            logger.error("Error leyendo el prompt (%s): %s. Usando fallback interno.", ruta, e)
        return fallback

    # --------------------------------------------------------------------
    # Utilidades de similitud
    # --------------------------------------------------------------------
    @staticmethod
    def calcular_similitud_matricial(vector_consulta: np.ndarray, matriz_vectores: np.ndarray) -> np.ndarray:
        norma_q = np.linalg.norm(vector_consulta)
        if norma_q == 0:
            return np.zeros(matriz_vectores.shape[0])

        q_norm = vector_consulta / norma_q
        normas_m = np.linalg.norm(matriz_vectores, axis=1)
        normas_m[normas_m == 0] = 1e-10

        matriz_norm = matriz_vectores / normas_m[:, np.newaxis]
        return np.dot(matriz_norm, q_norm)

    # --------------------------------------------------------------------
    # PASO 1: Nodos semánticos más relevantes (con score)
    # --------------------------------------------------------------------
    def _buscar_nodos_relevantes(self, emb_consulta: np.ndarray) -> List[tuple[str, float]]:
        embeddings_dict = self.indice.embeddings_store
        if not embeddings_dict:
            raise ValueError("El store de embeddings está vacío. Ejecuta primero la Etapa 3 (construcción del grafo).")

        node_ids = list(embeddings_dict.keys())
        matriz_embeddings = np.array(list(embeddings_dict.values()))

        similitudes = self.calcular_similitud_matricial(emb_consulta, matriz_embeddings)
        orden = np.argsort(similitudes)[::-1][:settings.TOP_K_NODOS]

        resultado = [
            (node_ids[idx], float(similitudes[idx]))
            for idx in orden
            if float(similitudes[idx]) >= settings.UMBRAL_SIMILITUD_NODO
        ]

        # Salvaguarda: si el umbral descarta todo, conservar al menos el mejor nodo.
        if not resultado and len(orden) > 0:
            mejor_idx = orden[0]
            resultado = [(node_ids[mejor_idx], float(similitudes[mejor_idx]))]

        logger.info("[1/4] Nodos relevantes seleccionados: %s",
                    [(n, round(s, 4)) for n, s in resultado])
        return resultado

    # --------------------------------------------------------------------
    # PASO 2: Candidatos de sección a partir de las 'apariciones' de los nodos
    # --------------------------------------------------------------------
    def _construir_candidatos_secciones(self, top_nodos: List[tuple[str, float]]) -> Dict[str, Dict[str, Any]]:
        candidatos: Dict[str, Dict[str, Any]] = {}

        for nodo_id, score in top_nodos:
            nodo = self.indice.nodos.get(nodo_id)
            if nodo is None:
                logger.info("Nodo %s sin trazabilidad de sección directa (probable CATEGORIA); se omite.", nodo_id)
                continue

            for aparicion in nodo.get("apariciones", []):
                seccion_id = aparicion.get("seccion_id")
                if not seccion_id:
                    continue

                sec_meta = self.indice.secciones.get(seccion_id)
                if not sec_meta:
                    continue

                documento_id = sec_meta.get("documento_id")
                dominio = self.indice.resolver_dominio_documento(documento_id)

                existente = candidatos.get(seccion_id)
                if existente is None or score > existente["score"]:
                    candidatos[seccion_id] = {
                        "seccion_id": seccion_id,
                        "documento_id": documento_id,
                        "documento_nombre": sec_meta.get("documento_nombre"),
                        "titulo_seccion": sec_meta.get("titulo"),
                        "ruta_jerarquica": self._sanear_ruta_jerarquica(sec_meta.get("ruta_jerarquica", [])),
                        "nivel": sec_meta.get("nivel", 1),
                        "dominio": dominio,
                        "score": score,
                        "nodo_origen": nodo_id,
                    }

        logger.info("[2/4] Secciones candidatas (vía apariciones de nodos): %d", len(candidatos))
        return candidatos

    # --------------------------------------------------------------------
    # Saneo defensivo de ruta_jerarquica (mitiga corrupción de Etapa 2/3)
    # --------------------------------------------------------------------
    @staticmethod
    def _sanear_ruta_jerarquica(ruta: List[str]) -> List[str]:
        """
        Defensa contra rutas jerárquicas corruptas (bloques de texto completo capturados
        como 'encabezado padre' por un parser de Markdown deficiente en etapas previas).
        Truncar cada elemento y conserva solo los N más cercanos a la sección (los últimos),
        que son los de mayor valor de trazabilidad real.
        """
        if not ruta:
            return []

        limitados = ruta[-settings.MAX_ITEMS_RUTA_JERARQUICA:]
        saneados = []
        for item in limitados:
            texto = str(item).strip()
            if len(texto) > settings.MAX_LONGITUD_ITEM_RUTA:
                texto = texto[:settings.MAX_LONGITUD_ITEM_RUTA].rstrip() + "…"
            saneados.append(texto)
        return saneados

    # --------------------------------------------------------------------
    # PASO 3: Selección por nivel (mínimo 2 de nivel 1-3, opcional 4-6, con fallback)
    #         + tope por documento + balance por dominio
    # --------------------------------------------------------------------
    def _seleccionar_secciones(self, candidatos: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        todas = sorted(candidatos.values(), key=lambda c: c["score"], reverse=True)

        # --- Tope por documento: evita que un solo documento/nodo acapare el contexto ---
        conteo_por_doc: Dict[str, int] = {}
        todas_filtradas: List[Dict[str, Any]] = []
        for c in todas:
            doc_id = c["documento_id"]
            usados = conteo_por_doc.get(doc_id, 0)
            if usados >= settings.MAX_SECCIONES_POR_DOCUMENTO:
                continue
            conteo_por_doc[doc_id] = usados + 1
            todas_filtradas.append(c)

        if len(todas_filtradas) < len(todas):
            logger.info(
                "Tope por documento aplicado: %d secciones descartadas por exceder %d por documento.",
                len(todas) - len(todas_filtradas), settings.MAX_SECCIONES_POR_DOCUMENTO
            )

        nivel_1_3 = [c for c in todas_filtradas if c["nivel"] in (1, 2, 3)]
        nivel_4_6 = [c for c in todas_filtradas if c["nivel"] in (4, 5, 6)]

        min_requerido = settings.MIN_SECCIONES_NIVEL_1_3
        cupo_total = settings.TOP_K_SECCIONES_FINAL
        seleccion: List[Dict[str, Any]] = []

        if len(nivel_1_3) >= min_requerido:
            seleccion.extend(nivel_1_3[:cupo_total])
            espacio_restante = cupo_total - len(seleccion)
            if espacio_restante > 0:
                opcionales = [c for c in nivel_4_6 if c["score"] >= settings.UMBRAL_NIVEL_4_6]
                seleccion.extend(opcionales[:espacio_restante])
            logger.info(
                "[3/4] Selección estándar: %d de nivel 1-3 + %d de nivel 4-6.",
                min(len(nivel_1_3), cupo_total),
                max(0, len(seleccion) - min(len(nivel_1_3), cupo_total))
            )
        else:
            logger.warning(
                "Solo %d secciones de nivel 1-3 disponibles (mínimo requerido: %d). "
                "Aplicando fallback por relevancia (score), ignorando el filtro de nivel.",
                len(nivel_1_3), min_requerido
            )
            seleccion.extend(todas_filtradas[:cupo_total])

        seleccion = self._balancear_por_dominio(seleccion, todas_filtradas, cupo_total)
        return seleccion

    @staticmethod
    def _balancear_por_dominio(
        seleccion: List[Dict[str, Any]],
        candidatos_filtrados: List[Dict[str, Any]],
        cupo_total: int,
    ) -> List[Dict[str, Any]]:
        """
        Garantiza representación mínima de cada dominio presente entre los candidatos
        (p. ej. si hay ISO y Leyes disponibles, ambos deben aparecer en el contexto final,
        incluso si el ranking puro por score habría excluido a uno de los dos).
        """
        dominios_presentes = {c["dominio"] for c in candidatos_filtrados if c["dominio"]}
        dominios_en_seleccion = {c["dominio"] for c in seleccion if c["dominio"]}
        dominios_faltantes = dominios_presentes - dominios_en_seleccion

        if not dominios_faltantes:
            return seleccion

        for dominio in dominios_faltantes:
            mejor_del_dominio = next(
                (c for c in candidatos_filtrados if c["dominio"] == dominio), None
            )
            if mejor_del_dominio is None:
                continue

            if len(seleccion) < cupo_total:
                seleccion.append(mejor_del_dominio)
            else:
                idx_peor = min(range(len(seleccion)), key=lambda i: seleccion[i]["score"])
                logger.info(
                    "Balance de dominio: reemplazando sección de menor score (%s, %.4f) "
                    "por candidato de dominio faltante '%s' (%s, %.4f).",
                    seleccion[idx_peor]["seccion_id"], seleccion[idx_peor]["score"],
                    dominio, mejor_del_dominio["seccion_id"], mejor_del_dominio["score"]
                )
                seleccion[idx_peor] = mejor_del_dominio

        return sorted(seleccion, key=lambda c: c["score"], reverse=True)

    # --------------------------------------------------------------------
    # PASO 4: Resolución de contenido + contexto con trazabilidad completa
    # --------------------------------------------------------------------
    def _resolver_contexto(self, secciones_seleccionadas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        contexto: List[Dict[str, Any]] = []

        for sec in secciones_seleccionadas:
            resuelto = self.indice.resolver_contenido_seccion(sec["seccion_id"])
            if not resuelto or not resuelto["texto"]:
                continue

            contexto.append({
                "seccion_id": sec["seccion_id"],
                "documento_id": sec["documento_id"],
                "documento_nombre": sec["documento_nombre"],
                "titulo_seccion": sec["titulo_seccion"],
                "ruta_jerarquica": sec["ruta_jerarquica"],
                "nivel": sec["nivel"],
                "dominio": resuelto["dominio"],
                "contenido": resuelto["texto"],
                "score": round(sec["score"], 4),
                "nodo_origen": sec["nodo_origen"],
            })

        logger.info("[4/4] Secciones con contenido resuelto para el contexto: %d", len(contexto))
        return contexto

    # --------------------------------------------------------------------
    # Orquestación de recuperación
    # --------------------------------------------------------------------
    def recuperar_contexto(self, consulta_usuario: str) -> List[Dict[str, Any]]:
        emb_consulta = self.modelo_emb.encode(consulta_usuario)

        top_nodos = self._buscar_nodos_relevantes(emb_consulta)
        candidatos = self._construir_candidatos_secciones(top_nodos)
        seleccionadas = self._seleccionar_secciones(candidatos)
        return self._resolver_contexto(seleccionadas)

    # --------------------------------------------------------------------
    # Generación de respuesta
    # --------------------------------------------------------------------
    def responder_consulta(self, consulta_usuario: str) -> Dict[str, Any]:
        inicio = time.perf_counter()
        contexto = self.recuperar_contexto(consulta_usuario)

        if not contexto:
            return {
                "respuesta": "No se encontró información suficiente para responder la consulta.",
                "trazabilidad": [],
                "tiempo_segundos": round(time.perf_counter() - inicio, 2),
            }

        bloque_contexto = "".join([
            f"\n--- SECCIÓN {i+1} "
            f"[Doc: {c['documento_nombre']} ({c['documento_id']}) | "
            f"Ruta: {' > '.join(c['ruta_jerarquica']) if c['ruta_jerarquica'] else c['titulo_seccion']} | "
            f"Nivel: {c['nivel']} | Dominio: {c['dominio']} | Score: {c['score']}] ---\n"
            f"{c['contenido']}\n"
            for i, c in enumerate(contexto)
        ])

        logger.info("Consultando a DeepSeek con %d secciones de contexto...", len(contexto))
        respuesta = self.client_llm.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": self.prompt_sistema},
                {"role": "user", "content": f"CONTEXTO:\n{bloque_contexto}\n\nPREGUNTA:\n{consulta_usuario}"}
            ],
            temperature=0.2
        )

        tiempo_total = time.perf_counter() - inicio
        logger.info("Consulta completada en %.2f segundos.", tiempo_total)

        return {
            "respuesta": respuesta.choices[0].message.content,
            "trazabilidad": [
                {
                    "seccion_id": c["seccion_id"],
                    "documento_id": c["documento_id"],
                    "documento_nombre": c["documento_nombre"],
                    "titulo_seccion": c["titulo_seccion"],
                    "ruta_jerarquica": c["ruta_jerarquica"],
                    "nivel": c["nivel"],
                    "dominio": c["dominio"],
                    "score": c["score"],
                }
                for c in contexto
            ],
            "tiempo_segundos": round(tiempo_total, 2),
        }


def ejecutar_etapa_4(pregunta: str) -> Dict[str, Any]:
    pipeline = PipelineGraphRAG()
    return pipeline.responder_consulta(pregunta)


# --------------------------------------------------------------------------
# Presentación en consola
# --------------------------------------------------------------------------
def _formatear_ruta(ruta: List[str]) -> str:
    return " > ".join(ruta) if ruta else "(sin ruta jerárquica)"


def imprimir_resultado(pregunta: str, resultado: Dict[str, Any]) -> None:
    ancho = 80

    print("\n" + "=" * ancho)
    print(f" PREGUNTA: {pregunta}")
    print("=" * ancho)

    print("\nRESPUESTA:")
    print("-" * ancho)
    for parrafo in resultado["respuesta"].split("\n"):
        if parrafo.strip():
            print(textwrap.fill(parrafo, width=ancho))
        else:
            print()

    trazabilidad = resultado.get("trazabilidad", [])
    print("\n" + "-" * ancho)
    print(f"TRAZABILIDAD ({len(trazabilidad)} secciones utilizadas):")
    print("-" * ancho)

    if not trazabilidad:
        print("  (sin fuentes — no se encontró contexto suficiente)")
    else:
        for i, t in enumerate(trazabilidad, start=1):
            print(f"\n  [{i}] {t['documento_nombre']}  (dominio: {t['dominio']}, nivel: {t['nivel']}, score: {t['score']})")
            print(f"      Sección : {t['titulo_seccion']}")
            print(f"      Ruta    : {_formatear_ruta(t['ruta_jerarquica'])}")
            print(f"      ID      : {t['seccion_id']}")

    print("\n" + "-" * ancho)
    print(f"Tiempo total: {resultado['tiempo_segundos']} s")
    print("=" * ancho + "\n")


if __name__ == "__main__":
    pipeline = PipelineGraphRAG()

    print("\nPipeline GraphRAG listo. Escribe tu pregunta (o 'salir' para terminar).\n")
    while True:
        try:
            pregunta = input("Pregunta > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSaliendo...")
            break

        if not pregunta:
            continue
        if pregunta.lower() in ("salir", "exit", "quit"):
            print("Saliendo...")
            break

        resultado = pipeline.responder_consulta(pregunta)
        imprimir_resultado(pregunta, resultado)