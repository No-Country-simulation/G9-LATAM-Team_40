"""
Script principal (Orquestador) de Retrieval y Generación Aumentada (RAG) basado en el Grafo Global.
Etapa 4: reutiliza los nodos (CAT / SEC / REL) ya construidos en la Etapa 3.
No re-embebe secciones ni re-filtra archivos crudos por consulta.

FLUJO:
    1. Embeber la consulta del usuario.
    2. Comparar contra embeddings_store (ids de CUALQUIER nivel: CAT/SEC/REL) -> top-K nodos.
    3. Por cada nodo top-K, subir por parent_id hasta su(s) nodo(s) SEC (nivel_2),
       y resolver el CONTENIDO REAL de cada referencia {documento_id, titulo} contra
       el archivo fuente '<documento_id>.secciones.json' (esto es lo que antes se
       llamaba "apariciones", pero ahora viene directo del árbol REL->SEC->CAT).
    4. Filtrar y priorizar candidatos (score, nivel, tope por documento, balance por dominio).
    5. Construir el contexto final con trazabilidad completa (documento_id, título,
       categoría, palabras clave, dominio, nivel, ruta_jerarquica, source_path).
    6. Enviar el contexto al LLM y devolver la respuesta + trazabilidad.
"""
from __future__ import annotations

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
        settings.validate_graph_rag_key()
        logger.info("Cargando índice del grafo, embeddings y contenido fuente...")
        self.indice = IndiceGrafo()
        if not self.indice.embeddings_store:
            raise RuntimeError(
                "No hay embeddings GraphRAG disponibles. Ejecuta `git lfs pull` "
                "o configura DATA_SOURCE=oci con los artefactos publicados."
            )
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
    # Los ids en embeddings_store pueden ser de CUALQUIER nivel: CAT, SEC o REL.
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
    # PASO 2: Candidatos de sección, recorriendo REL/SEC/CAT -> nodo(s) SEC
    # -> referencias {documento_id, titulo} -> contenido real resuelto contra
    # el archivo fuente. El nivel real de cada sección solo se conoce aquí
    # (viene del archivo fuente, no del grafo), por eso la resolución de
    # contenido ocurre en este paso y no al final.
    # --------------------------------------------------------------------
    def _construir_candidatos_secciones(self, top_nodos: List[tuple[str, float]]) -> Dict[str, Dict[str, Any]]:
        candidatos: Dict[str, Dict[str, Any]] = {}

        for nodo_id, score in top_nodos:
            nodos_sec = self.indice.resolver_nodos_seccion_desde_nodo(nodo_id)
            if not nodos_sec:
                logger.info("Nodo %s sin nodos SEC asociados; se omite.", nodo_id)
                continue

            for nodo_sec in nodos_sec:
                resueltos = self.indice.resolver_contenido_nodo_seccion(nodo_sec)

                for item in resueltos:
                    documento_id = item["documento_id"]
                    titulo_seccion = item["titulo_seccion"]
                    clave = f"{documento_id}::{titulo_seccion}"

                    existente = candidatos.get(clave)
                    if existente is None or score > existente["score"]:
                        info_doc = self.indice.obtener_info_documento(documento_id)
                        info_clasif = self.indice.obtener_categoria_y_palabras_clave(documento_id)
                        candidatos[clave] = {
                            "clave": clave,
                            "documento_id": documento_id,
                            "documento_titulo": info_doc.get("titulo") or documento_id,
                            "categoria": info_clasif.get("categoria", ""),
                            "palabras_clave": info_clasif.get("palabras_clave", []),
                            "titulo_seccion": titulo_seccion,
                            "ruta_jerarquica": self._sanear_ruta_jerarquica(item.get("ruta_jerarquica", [])),
                            "nivel": item.get("nivel") or 1,
                            "dominio": item["dominio"],
                            "contenido": item["texto"],
                            "source_path": item.get("source_path", ""),
                            "score": score,
                            "nodo_origen": nodo_sec.get("id"),
                        }

        logger.info("[2/4] Secciones candidatas (vía nodos SEC resueltos): %d", len(candidatos))
        return candidatos

    # --------------------------------------------------------------------
    # Saneo defensivo de ruta_jerarquica (mitiga corrupción de Etapa 2/3)
    # --------------------------------------------------------------------
    @staticmethod
    def _sanear_ruta_jerarquica(ruta: List[str]) -> List[str]:
        """
        Defensa contra rutas jerárquicas corruptas (bloques de texto completo capturados
        como 'encabezado padre' por un parser de Markdown deficiente en etapas previas).
        Trunca cada elemento y conserva solo los N más cercanos a la sección (los últimos),
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
                    seleccion[idx_peor]["clave"], seleccion[idx_peor]["score"],
                    dominio, mejor_del_dominio["clave"], mejor_del_dominio["score"]
                )
                seleccion[idx_peor] = mejor_del_dominio

        return sorted(seleccion, key=lambda c: c["score"], reverse=True)

    # --------------------------------------------------------------------
    # PASO 4: Formateo del contexto final (el contenido ya viene resuelto
    # desde el Paso 2; aquí solo se descartan candidatos sin texto y se
    # redondea el score para presentación).
    # --------------------------------------------------------------------
    @staticmethod
    def _formatear_contexto(secciones_seleccionadas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        contexto: List[Dict[str, Any]] = []

        for sec in secciones_seleccionadas:
            if not sec.get("contenido"):
                continue

            contexto.append({
                "documento_id": sec["documento_id"],
                "documento_titulo": sec["documento_titulo"],
                "categoria": sec.get("categoria", ""),
                "palabras_clave": sec.get("palabras_clave", []),
                "titulo_seccion": sec["titulo_seccion"],
                "ruta_jerarquica": sec["ruta_jerarquica"],
                "nivel": sec["nivel"],
                "dominio": sec["dominio"],
                "contenido": sec["contenido"],
                "source_path": sec.get("source_path", ""),
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
        return self._formatear_contexto(seleccionadas)

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
            f"[Doc: {c['documento_titulo']} ({c['documento_id']}) | "
            f"Categoría: {c['categoria'] or 'N/D'} | "
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
                    "documento_id": c["documento_id"],
                    "documento_titulo": c["documento_titulo"],
                    "categoria": c.get("categoria", ""),
                    "palabras_clave": c.get("palabras_clave", []),
                    "titulo_seccion": c["titulo_seccion"],
                    "ruta_jerarquica": c["ruta_jerarquica"],
                    "nivel": c["nivel"],
                    "dominio": c["dominio"],
                    "score": c["score"],
                    "source_path": c.get("source_path", ""),
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
        print("   (sin fuentes — no se encontró contexto suficiente)")
    else:
        for i, t in enumerate(trazabilidad, start=1):
            print(f"\n   [{i}] {t['documento_titulo']}  (dominio: {t['dominio']}, nivel: {t['nivel']}, score: {t['score']})")
            print(f"       Categoría      : {t.get('categoria') or '(sin categoría)'}")
            print(f"       Palabras clave : {', '.join(t.get('palabras_clave') or []) or '(sin palabras clave)'}")
            print(f"       Sección : {t['titulo_seccion']}")
            print(f"       Ruta    : {_formatear_ruta(t['ruta_jerarquica'])}")
            print(f"       Doc ID  : {t['documento_id']}")
            print(f"       Fuente  : {t.get('source_path') or '(sin source_path)'}")

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