"""Orquestador de recuperación GraphRAG sobre corpus BASE y overlay PRIVADO."""
from __future__ import annotations

import logging
import sys
import textwrap
import time
from typing import Any
from uuid import UUID

import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from settings import Settings, settings
from .indice_grafo import IndiceGrafo
from .tenant_registry import TenantIndexRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("MAIN_Etapa_4")


class PipelineGraphRAG:
    def __init__(
        self,
        config: Settings = settings,
        registry: TenantIndexRegistry | None = None,
    ):
        self.settings = config
        self.settings.validate_graph_rag_key()
        self.indice = IndiceGrafo(self.settings)
        if not self.indice.embeddings_store:
            raise RuntimeError("No hay embeddings GraphRAG disponibles para el corpus base.")
        self.registry = registry or TenantIndexRegistry(self.settings)
        self.modelo_emb = SentenceTransformer(self.settings.MODELO_EMBEDDINGS)
        self.client_llm = OpenAI(api_key=self.settings.DEEPSEEK_API_KEY, base_url=self.settings.DEEPSEEK_BASE_URL)
        self.prompt_sistema = self._cargar_prompt_sistema()

    def _cargar_prompt_sistema(self) -> str:
        fallback = (
            "Eres un consultor experto en normativas legales e ISO. "
            "Responde basándote ÚNICAMENTE en el contexto proporcionado."
        )
        try:
            texto = self.settings.PROMPT_RAG_SISTEMA_PATH.read_text(encoding="utf-8").strip()
            return texto or fallback
        except Exception as exc:
            logger.warning("No se pudo cargar el prompt GraphRAG: %s", exc)
            return fallback

    @staticmethod
    def calcular_similitud_matricial(vector_consulta: np.ndarray, matriz_vectores: np.ndarray) -> np.ndarray:
        norma_q = np.linalg.norm(vector_consulta)
        if norma_q == 0:
            return np.zeros(matriz_vectores.shape[0])
        q_norm = vector_consulta / norma_q
        normas = np.linalg.norm(matriz_vectores, axis=1)
        normas[normas == 0] = 1e-10
        return np.dot(matriz_vectores / normas[:, np.newaxis], q_norm)

    def _buscar_nodos_relevantes(self, emb_consulta: np.ndarray, indice: IndiceGrafo) -> list[tuple[str, float]]:
        if not indice.embeddings_store:
            return []
        node_ids = list(indice.embeddings_store)
        matriz = np.array(list(indice.embeddings_store.values()))
        similitudes = self.calcular_similitud_matricial(emb_consulta, matriz)
        orden = np.argsort(similitudes)[::-1][: self.settings.TOP_K_NODOS]
        resultado = [
            (node_ids[idx], float(similitudes[idx]))
            for idx in orden
            if float(similitudes[idx]) >= self.settings.UMBRAL_SIMILITUD_NODO
        ]
        if not resultado and len(orden) > 0:
            resultado = [(node_ids[orden[0]], float(similitudes[orden[0]]))]
        return resultado

    def _construir_candidatos_secciones(
        self,
        top_nodos: list[tuple[str, float]],
        indice: IndiceGrafo,
        corpus: str,
    ) -> dict[str, dict[str, Any]]:
        candidatos: dict[str, dict[str, Any]] = {}
        for nodo_id, score in top_nodos:
            for nodo_sec in indice.resolver_nodos_seccion_desde_nodo(nodo_id):
                for item in indice.resolver_contenido_nodo_seccion(nodo_sec):
                    documento_id = item["documento_id"]
                    titulo = item["titulo_seccion"]
                    clave = f"{corpus}::{documento_id}::{titulo}"
                    existente = candidatos.get(clave)
                    if existente is not None and score <= existente["score"]:
                        continue
                    info_doc = indice.obtener_info_documento(documento_id)
                    info_clasif = indice.obtener_categoria_y_palabras_clave(documento_id)
                    candidatos[clave] = {
                        "clave": clave,
                        "documento_id": documento_id,
                        "documento_titulo": info_doc.get("titulo") or documento_id,
                        "categoria": info_clasif.get("categoria") or "Sin categoría",
                        "palabras_clave": info_clasif.get("palabras_clave", []),
                        "titulo_seccion": titulo,
                        "ruta_jerarquica": self._sanear_ruta_jerarquica(item.get("ruta_jerarquica", [])),
                        "nivel": item.get("nivel") or 1,
                        "dominio": item.get("dominio", ""),
                        "contenido": item.get("texto", ""),
                        "score": score,
                        "nodo_origen": nodo_sec.get("id"),
                        "corpus": corpus,
                        "archivo_id": item.get("archivo_id") or info_doc.get("archivo_id"),
                    }
        return candidatos

    def _sanear_ruta_jerarquica(self, ruta: list[str]) -> list[str]:
        limitados = ruta[-self.settings.MAX_ITEMS_RUTA_JERARQUICA :] if ruta else []
        resultado = []
        for item in limitados:
            texto = str(item).strip()
            if len(texto) > self.settings.MAX_LONGITUD_ITEM_RUTA:
                texto = texto[: self.settings.MAX_LONGITUD_ITEM_RUTA].rstrip() + "…"
            resultado.append(texto)
        return resultado

    def _seleccionar_secciones(self, candidatos: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        todas = sorted(candidatos.values(), key=lambda item: item["score"], reverse=True)
        por_documento: dict[str, int] = {}
        filtradas = []
        for candidato in todas:
            key = f"{candidato['corpus']}::{candidato['documento_id']}"
            if por_documento.get(key, 0) >= self.settings.MAX_SECCIONES_POR_DOCUMENTO:
                continue
            por_documento[key] = por_documento.get(key, 0) + 1
            filtradas.append(candidato)

        nivel_1_3 = [c for c in filtradas if c["nivel"] in (1, 2, 3)]
        nivel_4_6 = [c for c in filtradas if c["nivel"] in (4, 5, 6)]
        cupo = self.settings.TOP_K_SECCIONES_FINAL
        if len(nivel_1_3) >= self.settings.MIN_SECCIONES_NIVEL_1_3:
            seleccion = nivel_1_3[:cupo]
            seleccion.extend([
                c for c in nivel_4_6 if c["score"] >= self.settings.UMBRAL_NIVEL_4_6
            ][: max(0, cupo - len(seleccion))])
        else:
            seleccion = filtradas[:cupo]
        return self._balancear_por_dominio(seleccion, filtradas, cupo)

    @staticmethod
    def _balancear_por_dominio(seleccion: list[dict[str, Any]], candidatos: list[dict[str, Any]], cupo: int) -> list[dict[str, Any]]:
        presentes = {c["dominio"] for c in candidatos if c.get("dominio")}
        usados = {c["dominio"] for c in seleccion if c.get("dominio")}
        for dominio in presentes - usados:
            mejor = next((c for c in candidatos if c.get("dominio") == dominio), None)
            if mejor is None:
                continue
            if len(seleccion) < cupo:
                seleccion.append(mejor)
            else:
                peor = min(range(len(seleccion)), key=lambda idx: seleccion[idx]["score"])
                seleccion[peor] = mejor
        return sorted(seleccion, key=lambda item: item["score"], reverse=True)

    def _formatear_contexto(self, seleccionadas: list[dict[str, Any]]) -> list[dict[str, Any]]:
        contexto = []
        for sec in seleccionadas:
            if not sec.get("contenido"):
                continue
            contexto.append({
                "documento_id": sec["documento_id"],
                "documento_titulo": sec["documento_titulo"],
                "categoria": sec["categoria"],
                "palabras_clave": sec["palabras_clave"],
                "titulo_seccion": sec["titulo_seccion"],
                "ruta_jerarquica": sec["ruta_jerarquica"],
                "nivel": sec["nivel"],
                "dominio": sec["dominio"],
                "contenido": sec["contenido"],
                "score": round(sec["score"], 4),
                "nodo_origen": sec["nodo_origen"],
                "corpus": sec["corpus"],
                "archivo_id": sec.get("archivo_id"),
            })
        return contexto

    def recuperar_contexto(self, consulta_usuario: str, user_id: UUID | None = None, emb_consulta: np.ndarray | None = None) -> list[dict[str, Any]]:
        embedding = emb_consulta if emb_consulta is not None else self.modelo_emb.encode(consulta_usuario)
        candidatos = self._construir_candidatos_secciones(
            self._buscar_nodos_relevantes(embedding, self.indice), self.indice, "BASE"
        )
        if user_id is not None:
            privado = self.registry.get(user_id)
            if privado is not None:
                candidatos.update(self._construir_candidatos_secciones(
                    self._buscar_nodos_relevantes(embedding, privado), privado, "PRIVADO"
                ))
        return self._formatear_contexto(self._seleccionar_secciones(candidatos))

    def responder_consulta(self, consulta_usuario: str, user_id: UUID | None = None) -> dict[str, Any]:
        inicio = time.perf_counter()
        embedding = self.modelo_emb.encode(consulta_usuario)
        contexto = self.recuperar_contexto(consulta_usuario, user_id, embedding)
        if not contexto:
            return {
                "respuesta": "No se encontró información suficiente para responder la consulta.",
                "trazabilidad": [],
                "tiempo_segundos": round(time.perf_counter() - inicio, 2),
            }

        bloque = "".join(
            f"\n--- SECCIÓN {i + 1} [Corpus: {c['corpus']} | Doc: {c['documento_titulo']} "
            f"({c['documento_id']}) | Categoría: {c['categoria']} | "
            f"Ruta: {' > '.join(c['ruta_jerarquica']) if c['ruta_jerarquica'] else c['titulo_seccion']} | "
            f"Nivel: {c['nivel']} | Dominio: {c['dominio']} | Score: {c['score']}] ---\n{c['contenido']}\n"
            for i, c in enumerate(contexto)
        )
        respuesta = self.client_llm.chat.completions.create(
            model=self.settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": self.prompt_sistema},
                {"role": "user", "content": f"CONTEXTO:\n{bloque}\n\nPREGUNTA:\n{consulta_usuario}"},
            ],
            temperature=0.2,
        )
        tiempo = round(time.perf_counter() - inicio, 2)
        return {
            "respuesta": respuesta.choices[0].message.content,
            "trazabilidad": [
                {
                    "documento_id": c["documento_id"],
                    "documento_titulo": c["documento_titulo"],
                    "categoria": c["categoria"],
                    "palabras_clave": c["palabras_clave"],
                    "titulo_seccion": c["titulo_seccion"],
                    "ruta_jerarquica": c["ruta_jerarquica"],
                    "nivel": c["nivel"],
                    "dominio": c["dominio"],
                    "score": c["score"],
                    "corpus": c["corpus"],
                    "archivo_id": c.get("archivo_id"),
                }
                for c in contexto
            ],
            "tiempo_segundos": tiempo,
        }


def ejecutar_etapa_4(pregunta: str) -> dict[str, Any]:
    return PipelineGraphRAG().responder_consulta(pregunta)


def _formatear_ruta(ruta: list[str]) -> str:
    return " > ".join(ruta) if ruta else "(sin ruta jerárquica)"


def imprimir_resultado(pregunta: str, resultado: dict[str, Any]) -> None:
    ancho = 80
    print("\n" + "=" * ancho)
    print(f" PREGUNTA: {pregunta}")
    print("=" * ancho)
    print("\nRESPUESTA:\n" + "-" * ancho)
    for parrafo in resultado["respuesta"].split("\n"):
        print(textwrap.fill(parrafo, width=ancho) if parrafo.strip() else "")
    trazabilidad = resultado.get("trazabilidad", [])
    print(f"\nTRAZABILIDAD ({len(trazabilidad)} secciones utilizadas):\n" + "-" * ancho)
    for i, trace in enumerate(trazabilidad, start=1):
        print(f"\n   [{i}] {trace['documento_titulo']} ({trace['corpus']}, score: {trace['score']})")
        print(f"       Categoría      : {trace.get('categoria') or '(sin categoría)'}")
        print(f"       Sección        : {trace['titulo_seccion']}")
        print(f"       Ruta           : {_formatear_ruta(trace['ruta_jerarquica'])}")
        print(f"       Doc ID         : {trace['documento_id']}")
    print(f"\nTiempo total: {resultado['tiempo_segundos']} s\n" + "=" * ancho)


if __name__ == "__main__":
    pipeline = PipelineGraphRAG()
    while True:
        try:
            pregunta = input("Pregunta > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if pregunta.lower() in ("salir", "exit", "quit"):
            break
        if pregunta:
            imprimir_resultado(pregunta, pipeline.responder_consulta(pregunta))
