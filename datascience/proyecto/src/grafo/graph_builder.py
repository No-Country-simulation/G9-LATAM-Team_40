from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from settings import settings
from .filtros import normalizar_key

logger = logging.getLogger("GraphRAGBuilder")

# Umbrales de similitud coseno para decidir si una sección/relación nueva
# se une a un nodo existente o crea uno nuevo. Ajustar según pruebas reales.
UMBRAL_SIMILITUD_N2 = 0.72
UMBRAL_SIMILITUD_N3 = 0.75


class GraphRAGBuilder:

    def __init__(self, ruta_grafo: Path, ruta_embeddings: Path):
        self.ruta_grafo = ruta_grafo
        self.ruta_embeddings = ruta_embeddings

        # Modelo de embeddings
        self.modelo_embeddings = SentenceTransformer(settings.MODELO_EMBEDDINGS)

        # ==========================================
        # ESTRUCTURA DEL GRAFO JERÁRQUICO
        # ==========================================
        self.nivel_1_categorias: dict[str, dict] = {}
        self.nivel_2_subcategorias: dict[str, dict] = {}
        self.nivel_3_relaciones: dict[str, dict] = {}
        self.embeddings_store: dict[str, list] = {}

        # Cargar información existente
        self.embeddings_store = self._cargar_store_embeddings()
        self._cargar_grafo_existente()

    # ==========================================================
    # UTILIDADES
    # ==========================================================

    def _generar_id_hash(self, base_string: str, prefijo: str) -> str:
        """Genera un ID determinístico basado en contenido."""
        hash_obj = hashlib.md5(base_string.encode("utf-8")).hexdigest()
        return f"{prefijo}_{hash_obj[:12]}"

    def _normalizar_cluster_id(self, cluster_id: str, categoria: str) -> str:
        """Usa el cluster_id original o genera uno a partir de la categoría."""
        if cluster_id:
            return normalizar_key(cluster_id)
        if normalizar_key(categoria) in {"SIN_CATEGORIA", "SINCATEGORIA"}:
            return "CAT_SINCATEGORIA"
        return f"CAT_{normalizar_key(categoria)}"

    def _generar_descripcion_categoria(
        self, categoria: str, palabras_claves: list[str]
    ) -> str:
        """Genera una descripción simple basada en categoría y palabras clave."""
        if palabras_claves:
            keywords = ", ".join(palabras_claves[:8])
            return (
                f"Categoría temática relacionada con {categoria.lower()}, "
                f"incluyendo conceptos como: {keywords}."
            )
        return f"Categoría temática: {categoria}."

    # ==========================================================
    # EMBEDDINGS Y PERSISTENCIA
    # ==========================================================

    def _cargar_store_embeddings(self) -> dict:
        """Carga embeddings previamente generados."""
        if self.ruta_embeddings.exists():
            try:
                return json.loads(self.ruta_embeddings.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("Error al cargar embeddings: %s", e)
        return {}

    def guardar_store_embeddings(self) -> None:
        """Guarda los embeddings en disco."""
        self.ruta_embeddings.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_embeddings.write_text(
            json.dumps(self.embeddings_store, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _cargar_grafo_existente(self) -> None:
        """Carga un grafo previamente construido desde disco."""
        if not self.ruta_grafo.exists():
            return

        try:
            data = json.loads(self.ruta_grafo.read_text(encoding="utf-8"))
            grafo = data.get("grafo_conceptual", {})

            self.nivel_1_categorias = {
                nodo["id"]: nodo for nodo in grafo.get("nivel_1_categorias", [])
            }
            self.nivel_2_subcategorias = {
                nodo["id"]: nodo for nodo in grafo.get("nivel_2_subcategorias", [])
            }
            self.nivel_3_relaciones = {
                nodo["id"]: nodo for nodo in grafo.get("nivel_3_relaciones", [])
            }

            logger.info(
                "Grafo existente cargado: %d categorías, %d secciones, %d relaciones.",
                len(self.nivel_1_categorias),
                len(self.nivel_2_subcategorias),
                len(self.nivel_3_relaciones),
            )

        except Exception as e:
            logger.error(
                "Error al cargar grafo existente: %s. Se iniciará un nuevo grafo.", e
            )
            self.nivel_1_categorias = {}
            self.nivel_2_subcategorias = {}
            self.nivel_3_relaciones = {}

    # ==========================================================
    # PROCESAMIENTO PRINCIPAL
    # ==========================================================

    def _agrupar_secciones_semanticamente(
        self, secciones: list[dict], cluster_id: str
    ) -> list[dict]:
        """Agrupa secciones nuevas comparando su embedding (similitud coseno)
        contra los nodos N2 YA EXISTENTES bajo este cluster_id (por id). Si
        ninguno supera el umbral, la sección se vuelve el ancla de un grupo
        nuevo (mismo comportamiento de creación que antes)."""
        if not secciones:
            return []

        vectores = self.modelo_embeddings.encode(
            [s["titulo"] for s in secciones],
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        # Candidatos = nodos N2 ya persistidos bajo esta categoría, con embedding disponible
        candidatos: dict[str, list] = {
            nodo["titulo_nodo_2"]: self.embeddings_store[sec_id]
            for sec_id, nodo in self.nivel_2_subcategorias.items()
            if nodo["parent_id"] == cluster_id and sec_id in self.embeddings_store
        }

        grupos: dict[str, list[dict]] = {}

        for seccion, vector in zip(secciones, vectores):
            vector = vector.tolist()
            mejor_titulo, mejor_sim = None, 0.0

            for titulo_candidato, vector_candidato in candidatos.items():
                sim = float(np.dot(vector, vector_candidato))
                if sim > mejor_sim:
                    mejor_sim, mejor_titulo = sim, titulo_candidato

            if mejor_titulo is not None and mejor_sim >= UMBRAL_SIMILITUD_N2:
                titulo_grupo = mejor_titulo
            else:
                titulo_grupo = seccion["titulo"]
                # queda disponible para comparar contra las siguientes secciones de este mismo lote
                candidatos[titulo_grupo] = vector

            grupos.setdefault(titulo_grupo, []).append(seccion)

        return [{"titulo": titulo, "secciones": secs} for titulo, secs in grupos.items()]

    def _agrupar_relaciones_semanticamente(
        self, relaciones: list[dict], sec_id: str
    ) -> list[dict]:
        """Mismo criterio que _agrupar_secciones_semanticamente, pero para
        relaciones dentro de un nodo N2 (sec_id) puntual."""
        if not relaciones:
            return []

        titulos = [
            f'{item["relacion"].get("sujeto", "")} → {item["relacion"].get("objeto", "")}'
            for item in relaciones
        ]
        vectores = self.modelo_embeddings.encode(
            titulos,batch_size=settings.BATCH_SIZE_EMBEDDINGS, normalize_embeddings=True, show_progress_bar=False
        )

        candidatos: dict[str, list] = {
            nodo["titulonodo_nivel_3"]: self.embeddings_store[rel_id]
            for rel_id, nodo in self.nivel_3_relaciones.items()
            if nodo["parent_id"] == sec_id and rel_id in self.embeddings_store
        }

        grupos: dict[str, list[dict]] = {}

        for item, titulo_item, vector in zip(relaciones, titulos, vectores):
            vector = vector.tolist()
            mejor_titulo, mejor_sim = None, 0.0

            for titulo_candidato, vector_candidato in candidatos.items():
                sim = float(np.dot(vector, vector_candidato))
                if sim > mejor_sim:
                    mejor_sim, mejor_titulo = sim, titulo_candidato

            if mejor_titulo is not None and mejor_sim >= UMBRAL_SIMILITUD_N3:
                titulo_grupo = mejor_titulo
            else:
                titulo_grupo = titulo_item
                candidatos[titulo_grupo] = vector

            grupos.setdefault(titulo_grupo, []).append(item)

        return [{"titulo": titulo, "relaciones": items} for titulo, items in grupos.items()]

    # ------------------------------------------------------------------
    # Fusión defensiva de referencias en nodos ya existentes (evita que
    # una colisión de hash (mismo título -> mismo sec_id/rel_id) borre o
    # ignore silenciosamente las referencias de un documento nuevo.
    # ------------------------------------------------------------------
    @staticmethod
    def _fusionar_secciones_nodo(nodo_n2: dict, secciones_grupo: list[dict]) -> None:
        """Agrega a nodo_n2['secciones'] las referencias {documento_id, titulo}
        de secciones_grupo que todavía no estén presentes (dedup por par)."""
        existentes = {
            (s.get("documento_id"), s.get("titulo"))
            for s in nodo_n2.get("secciones", [])
        }

        for s in secciones_grupo:
            clave = (s["documento_id"], s["titulo"])
            if clave in existentes:
                continue
            nodo_n2.setdefault("secciones", []).append({
                "documento_id": s["documento_id"],
                "titulo": s["titulo"],
            })
            existentes.add(clave)

    @staticmethod
    def _fusionar_relaciones_nodo(nodo_n3: dict, relaciones_grupo: list[dict]) -> None:
        """Agrega a nodo_n3['relaciones'] las relaciones de relaciones_grupo que
        todavía no estén presentes (dedup por contenido completo, ya que una
        relación no tiene un id propio más allá de sus campos)."""
        existentes = {
            json.dumps(r, sort_keys=True, ensure_ascii=False)
            for r in nodo_n3.get("relaciones", [])
        }

        for r in relaciones_grupo:
            nueva = {
                "documento_id": r["documento_id"],
                "titulo_seccion": r["titulo_seccion"],
                **r["relacion"],
            }
            clave = json.dumps(nueva, sort_keys=True, ensure_ascii=False)
            if clave in existentes:
                continue
            nodo_n3.setdefault("relaciones", []).append(nueva)
            existentes.add(clave)

    def procesar_categoria(self, categoria: str, documentos: list[dict],
                            documentos_categoria: list[dict]) -> None:
        """Construye N1 por categoría, N2 por agrupación semántica de secciones y N3 por agrupación semántica de relaciones."""

        if not categoria or not documentos:
            return

        # NIVEL 1: CATEGORÍA
        cluster_id = self._normalizar_cluster_id("", categoria)

        if cluster_id not in self.nivel_1_categorias:
            confianzas = [d.get("confianza", 1.0) for d in documentos_categoria]
            self.nivel_1_categorias[cluster_id] = {
                "id": cluster_id,
                "titulo": categoria,
                "confianza": sum(confianzas) / len(confianzas) if confianzas else 1.0
            }

        # SECCIONES DE TODOS LOS DOCUMENTOS DE LA CATEGORÍA
        secciones = []
        for doc in documentos:
            for seccion in doc.get("secciones", []):
                titulo = seccion.get("titulo", "").strip()
                if titulo:
                    secciones.append({
                        "documento_id": doc.get("documento_id"),
                        "titulo": titulo,
                        "nivel": seccion.get("nivel"),
                        "ruta_jerarquica": seccion.get("ruta_jerarquica", []),
                        "relaciones": seccion.get("relaciones", [])
                    })

        # NIVEL 2: AGRUPAR TÍTULOS SEMÁNTICAMENTE (contra nodos existentes por id)
        grupos_n2 = self._agrupar_secciones_semanticamente(secciones, cluster_id)

        for grupo in grupos_n2:
            titulo_n2 = grupo["titulo"]
            secciones_grupo = grupo["secciones"]

            sec_id = self._generar_id_hash(f"{cluster_id}|{titulo_n2}", "SEC")

            if sec_id not in self.nivel_2_subcategorias:
                self.nivel_2_subcategorias[sec_id] = {
                    "id": sec_id,
                    "parent_id": cluster_id,
                    "titulo_nodo_2": titulo_n2,
                    "secciones": [],
                }
                # El embedding se guarda de inmediato para que, dentro de la misma
                # corrida, otros documentos ya puedan compararse contra este nodo.
                if sec_id not in self.embeddings_store:
                    vector_ancla = self.modelo_embeddings.encode(
                        titulo_n2,batch_size=settings.BATCH_SIZE_EMBEDDINGS, normalize_embeddings=True, show_progress_bar=False
                    )
                    self.embeddings_store[sec_id] = vector_ancla.tolist()

            # FIX (antes se perdía si el nodo ya existía por colisión de título):
            # se fusionan las referencias nuevas dentro del nodo existente.
            self._fusionar_secciones_nodo(self.nivel_2_subcategorias[sec_id], secciones_grupo)

            # RELACIONES DE LAS SECCIONES DEL N2
            relaciones = []
            for seccion in secciones_grupo:
                for relacion in seccion.get("relaciones", []):
                    sujeto = relacion.get("sujeto", "").strip()
                    objeto = relacion.get("objeto", "").strip()

                    if sujeto and objeto:
                        relaciones.append({
                            "documento_id": seccion["documento_id"],
                            "titulo_seccion": seccion["titulo"],
                            "relacion": relacion
                        })

            # NIVEL 3: AGRUPAR RELACIONES SEMÁNTICAMENTE DENTRO DEL N2 (contra nodos existentes por id)
            grupos_n3 = self._agrupar_relaciones_semanticamente(relaciones, sec_id)

            for grupo_n3 in grupos_n3:
                titulo_n3 = grupo_n3["titulo"]
                relaciones_grupo = grupo_n3["relaciones"]

                rel_id = self._generar_id_hash(f"{sec_id}|{titulo_n3}", "REL")

                if rel_id not in self.nivel_3_relaciones:
                    self.nivel_3_relaciones[rel_id] = {
                        "id": rel_id,
                        "parent_id": sec_id,
                        "titulonodo_nivel_3": titulo_n3,
                        "relaciones": [],
                    }
                    if rel_id not in self.embeddings_store:
                        vector_ancla = self.modelo_embeddings.encode(
                            titulo_n3,batch_size=settings.BATCH_SIZE_EMBEDDINGS, normalize_embeddings=True, show_progress_bar=False
                        )
                        self.embeddings_store[rel_id] = vector_ancla.tolist()

                # FIX: mismo criterio que en N2, se fusionan en vez de descartar.
                self._fusionar_relaciones_nodo(self.nivel_3_relaciones[rel_id], relaciones_grupo)

    # ==========================================================
    # GESTIÓN DE EMBEDDINGS
    # ==========================================================
    def recolectar_nodos_sin_embedding(self) -> dict[str, str]:
        pendientes = {}

        for nodo in self.nivel_1_categorias.values():
            nodo_id = nodo["id"]
            texto = nodo.get("titulo", "")
            if nodo_id not in self.embeddings_store and texto:
                pendientes[nodo_id] = texto

        for nodo in self.nivel_2_subcategorias.values():
            nodo_id = nodo["id"]
            texto = nodo.get("titulo_nodo_2", "")
            if nodo_id not in self.embeddings_store and texto:
                pendientes[nodo_id] = texto

        for nodo in self.nivel_3_relaciones.values():
            nodo_id = nodo["id"]
            texto = nodo.get("titulonodo_nivel_3", "")
            if nodo_id not in self.embeddings_store and texto:
                pendientes[nodo_id] = texto

        return pendientes

    def generar_y_guardar_embeddings(self) -> None:
        """Genera y almacena vectores de embedding de forma incremental.
        Ahora también actúa como red de seguridad: la mayoría de los nodos
        nuevos ya quedaron con su embedding guardado desde procesar_categoria."""
        nodos_pendientes = self.recolectar_nodos_sin_embedding()

        if not nodos_pendientes:
            logger.info("No hay nodos nuevos para generar embeddings.")
            self.guardar_store_embeddings()
            return

        ids = list(nodos_pendientes.keys())
        textos = list(nodos_pendientes.values())

        logger.info("Generando %d embeddings nuevos...", len(textos))
        vectores = self.modelo_embeddings.encode(
            textos, batch_size=settings.BATCH_SIZE_EMBEDDINGS,
normalize_embeddings=True, show_progress_bar=False
        )

        for nodo_id, vector in zip(ids, vectores):
            self.embeddings_store[nodo_id] = vector.tolist()

        self.guardar_store_embeddings()
        logger.info("Embeddings guardados correctamente.")

    # ==========================================================
    # GUARDAR GRAFO FINAL
    # ==========================================================

    def guardar_grafo(self) -> None:
        """Exporta el grafo estructurado en formato JSON a disco."""
        grafo_json = {
            "grafo_conceptual": {
                "nivel_1_categorias": list(self.nivel_1_categorias.values()),
                "nivel_2_subcategorias": list(self.nivel_2_subcategorias.values()),
                "nivel_3_relaciones": list(self.nivel_3_relaciones.values()),
            }
        }

        self.ruta_grafo.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_grafo.write_text(
            json.dumps(grafo_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        logger.info("Grafo guardado correctamente: %s", self.ruta_grafo)