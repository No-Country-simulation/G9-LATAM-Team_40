import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

# ------------------------------------------------------------------------------
# IMPORTACIÓN DE CONFIGURACIÓN CENTRALIZADA Y MÓDULOS LOCALES
# ------------------------------------------------------------------------------
from settings import settings
from .indice_grafo import IndiceGrafo

# ------------------------------------------------------------------------------
# CONFIGURACIÓN DE LOGGING
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Etapa_4_Retrieval_RAG")


class PipelineGraphRAG:
    def __init__(self):
        logger.info("Cargando índice del grafo y embeddings...")
        self.indice = IndiceGrafo()  # Utiliza IndiceGrafo para cargar grafo y vectores
        
        logger.info("Cargando modelo de embeddings '%s'...", settings.MODELO_EMBEDDINGS)
        self.modelo_emb = SentenceTransformer(settings.MODELO_EMBEDDINGS)
        
        self.client_llm = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )

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

    def recuperar_contexto_dos_niveles(self, consulta_usuario: str) -> List[Dict[str, Any]]:
        logger.info("[1/4] Vectorizando consulta...")
        emb_consulta = self.modelo_emb.encode(consulta_usuario)

        # ----------------------------------------------------------------------
        # PASO 1: Búsqueda Vectorial en Nodos usando IndiceGrafo
        # ----------------------------------------------------------------------
        logger.info("[2/4] Buscando similitud en embeddings del grafo...")
        embeddings_dict = self.indice.embeddings_store
        if not embeddings_dict:
            raise ValueError("El store de embeddings está vacío en IndiceGrafo.")

        node_ids = list(embeddings_dict.keys())
        matriz_embeddings = np.array(list(embeddings_dict.values()))

        similitudes_nodos = self.calcular_similitud_matricial(emb_consulta, matriz_embeddings)
        top_indices_nodos = np.argsort(similitudes_nodos)[::-1][:settings.TOP_K_NODOS]
        top_nodos_ids = {node_ids[idx] for idx in top_indices_nodos}

        logger.info("Top %d Nodos seleccionados: %s", len(top_nodos_ids), list(top_nodos_ids))

        # ----------------------------------------------------------------------
        # PASO 2: Mapeo de Archivos Objetivo desde IndiceGrafo
        # ----------------------------------------------------------------------
        archivos_objetivo = set()
        for nodo_id in top_nodos_ids:
            nodo = self.indice.nodos.get(nodo_id, {})
            archivos = nodo.get("archivos_ids") or nodo.get("documentos") or nodo.get("archivos", [])
            if isinstance(archivos, str):
                archivos = [archivos]
            archivos_objetivo.update(map(str, archivos))

        logger.info("Documentos objetivo identificados (%d): %s", len(archivos_objetivo), list(archivos_objetivo))

        # ----------------------------------------------------------------------
        # PASO 3: Filtrado y Re-ranking de Secciones
        # ----------------------------------------------------------------------
        logger.info("[3/4] Aplanando y filtrando secciones...")
        secciones_totales = []
        for ruta_json, dominio in [(settings.ENTIDADES_LEYES_JSON, "Leyes"), (settings.ENTIDADES_ISOS_JSON, "ISOs")]:
            if ruta_json.exists():
                datos = json.loads(ruta_json.read_text(encoding="utf-8"))
                documentos = datos if isinstance(datos, list) else datos.get("documentos", [])
                for doc in documentos:
                    doc_id = str(doc.get("documento_id") or doc.get("documento_nombre") or "")
                    for sec in doc.get("secciones", []):
                        texto = sec.get("contenido") or sec.get("texto") or sec.get("texto_seccion") or sec.get("titulo", "")
                        if texto and str(texto).strip():
                            secciones_totales.append({
                                "documento_id": doc_id,
                                "origen_dominio": dominio,
                                "titulo_seccion": str(texto)[:80] + "...",
                                "texto_seccion": str(texto).strip()
                            })

        secciones_candidatas = [
            sec for sec in secciones_totales
            if not archivos_objetivo or sec["documento_id"] in archivos_objetivo
        ] or secciones_totales

        textos_secciones = [sec["texto_seccion"] for sec in secciones_candidatas]
        embeddings_secciones = self.modelo_emb.encode(textos_secciones, show_progress_bar=False)

        similitudes_secciones = self.calcular_similitud_matricial(emb_consulta, np.array(embeddings_secciones))
        top_indices_secciones = np.argsort(similitudes_secciones)[::-1][:settings.TOP_K_SECCIONES_FINAL]

        return [
            {
                "documento_id": secciones_candidatas[idx]["documento_id"],
                "dominio": secciones_candidatas[idx]["origen_dominio"],
                "titulo_seccion": secciones_candidatas[idx]["titulo_seccion"],
                "contenido": secciones_candidatas[idx]["texto_seccion"],
                "score": float(similitudes_secciones[idx])
            }
            for idx in top_indices_secciones
        ]

    def responder_consulta(self, consulta_usuario: str) -> str:
        inicio = time.perf_counter()
        secciones = self.recuperar_contexto_dos_niveles(consulta_usuario)

        if not secciones:
            return "No se encontró información suficiente para responder la consulta."

        bloque_contexto = "".join([
            f"\n--- SECCIÓN {i+1} [Origen: {s['dominio']} | Doc: {s['documento_id']} | Score: {s['score']:.4f}] ---\n{s['contenido']}\n"
            for i, s in enumerate(secciones)
        ])

        prompt_sistema = (
            "Eres un consultor experto en normativas legales e ISO. "
            "Responde basándote ÚNICAMENTE en el contexto. "
            "Diferencia explícitamente los requisitos legales de las exigencias ISO."
        )

        logger.info("[4/4] Consultando a DeepSeek...")
        respuesta = self.client_llm.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"CONTEXTO:\n{bloque_contexto}\n\nPREGUNTA:\n{consulta_usuario}"}
            ],
            temperature=0.2
        )

        logger.info("Consulta completada en %.2f segundos.", time.perf_counter() - inicio)
        return respuesta.choices[0].message.content


def ejecutar_etapa_4(pregunta: str) -> str:
    pipeline = PipelineGraphRAG()
    return pipeline.responder_consulta(pregunta)


if __name__ == "__main__":
    pregunta = "¿Cuáles son las principales exigencias legales e ISO identificadas en los documentos?"
    print("\n" + "=" * 80)
    print(ejecutar_etapa_4(pregunta))
    print("=" * 80)