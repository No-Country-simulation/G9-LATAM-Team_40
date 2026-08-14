from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
import networkx as nx
from sentence_transformers import SentenceTransformer

from settings import settings
from .filtros import es_texto_valido, normalizar_key

logger = logging.getLogger("GraphRAGBuilder")


class GraphRAGBuilder:
    def __init__(self, ruta_grafo: Path, ruta_embeddings: Path):
        self.ruta_grafo = ruta_grafo
        self.ruta_embeddings = ruta_embeddings
        self.modelo_embeddings = SentenceTransformer(settings.MODELO_EMBEDDINGS)
        self.G = self._cargar_grafo_existente()
        self.embeddings_store = self._cargar_store_embeddings()

    def _cargar_store_embeddings(self) -> dict:
        if self.ruta_embeddings.exists():
            try:
                return json.loads(self.ruta_embeddings.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("Error al cargar embeddings guardados: %s", e)
        return {}

    def guardar_store_embeddings(self) -> None:
        self.ruta_embeddings.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_embeddings.write_text(
            json.dumps(self.embeddings_store, ensure_ascii=False),
            encoding="utf-8",
        )

    def _cargar_grafo_existente(self) -> nx.MultiDiGraph:
        G = nx.MultiDiGraph()
        if not self.ruta_grafo.exists():
            G.add_node(settings.ROOT_ID, label="Corpus Normativo General ISO/Leyes", tipo="RAIZ", nivel=0)
            return G

        try:
            data = json.loads(self.ruta_grafo.read_text(encoding="utf-8"))
            for n in data.get("nodos", []):
                node_id = n.pop("id")
                G.add_node(node_id, **n)

            for a in data.get("aristas", []):
                origen, destino = a.pop("origen"), a.pop("destino")
                key = a.pop("edge_key", None)
                G.add_edge(origen, destino, key=key, **a)

            if settings.ROOT_ID not in G:
                G.add_node(settings.ROOT_ID, label="Corpus Normativo General ISO/Leyes", tipo="RAIZ", nivel=0)

        except Exception as e:
            logger.error("Error al cargar el grafo existente: %s. Creando nuevo.", e)
            G.add_node(settings.ROOT_ID, label="Corpus Normativo General ISO/Leyes", tipo="RAIZ", nivel=0)

        return G

    def guardar_grafo(self) -> None:
        self.ruta_grafo.parent.mkdir(parents=True, exist_ok=True)
        nodos_export = [{"id": n, **data} for n, data in self.G.nodes(data=True)]
        aristas_export = [
            {"edge_key": key, **data, "origen": u, "destino": v}
            for u, v, key, data in self.G.edges(keys=True, data=True)
        ]

        grafo_json = {
            "metadata": {
                "version": "GraphRAG-v4.2-optimizado",
                "actualizado": datetime.now().isoformat(),
                "total_nodos": self.G.number_of_nodes(),
                "total_aristas": self.G.number_of_edges(),
            },
            "nodos": nodos_export,
            "aristas": aristas_export,
        }
        self.ruta_grafo.write_text(
            json.dumps(grafo_json, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def documento_ya_en_grafo(self, document_id: str) -> bool:
        return self.G.has_node(f"SUBNODO_DOC_{document_id}")

    @staticmethod
    def construir_mapa_entidades_seccion(entidades: list[dict]) -> dict[str, str]:
        mapa = {}
        for e in entidades:
            canonical = e.get("canonical", "").strip()
            texto = e.get("texto", "").strip()
            if canonical and es_texto_valido(canonical):
                mapa[normalizar_key(canonical)] = canonical
                if texto:
                    mapa[normalizar_key(texto)] = canonical
        return mapa

    @staticmethod
    def obtener_identificador(doc: dict, tipo: str, idx: int) -> tuple[str, str]:
        document_id = (
            doc.get("documento_id")
            or doc.get("metadata", {}).get("archivo")
            or f"{tipo}_{idx}"
        )
        documento_nombre = doc.get("documento_nombre") or document_id
        return str(document_id), str(documento_nombre)

    def recolectar_entidades_nuevas(self, doc: dict) -> dict[str, str]:
        nuevas: dict[str, str] = {}
        for sec in doc.get("secciones", []):
            entidades = sec.get("entidades", [])
            mapa_entidades_seccion = self.construir_mapa_entidades_seccion(entidades)

            for e in entidades:
                canonical = e.get("canonical", "").strip()
                if canonical and es_texto_valido(canonical):
                    entity_id = f"ENT_{normalizar_key(canonical)}"
                    if not self.G.has_node(entity_id) and entity_id not in nuevas:
                        nuevas[entity_id] = canonical

            for rel in sec.get("relaciones", []):
                confianza = rel.get("confianza")
                if confianza is not None and confianza < settings.CONFIANZA_MINIMA_RELACION:
                    continue

                sujeto_txt = rel.get("sujeto", "").strip()
                objeto_txt = rel.get("objeto", "").strip()
                if not es_texto_valido(sujeto_txt) or not es_texto_valido(objeto_txt):
                    continue

                sujeto_canonical = mapa_entidades_seccion.get(
                    normalizar_key(sujeto_txt), sujeto_txt
                )
                objeto_canonical = mapa_entidades_seccion.get(
                    normalizar_key(objeto_txt), objeto_txt
                )

                for canonical in (sujeto_canonical, objeto_canonical):
                    entity_id = f"ENT_{normalizar_key(canonical)}"
                    if not self.G.has_node(entity_id) and entity_id not in nuevas:
                        nuevas[entity_id] = canonical

        return nuevas

    def procesar_documento(self, doc: dict, tipo: str, idx: int) -> None:
        document_id, documento_nombre = self.obtener_identificador(doc, tipo, idx)
        subnodo_doc_id = f"SUBNODO_DOC_{document_id}"

        self.G.add_node(
            subnodo_doc_id,
            label=documento_nombre,
            tipo="SUBNODO_DOCUMENTO",
            nivel=2,
            document_id=document_id,
            documento_nombre=documento_nombre,
            tipo_documento=tipo,
        )

        for clasif in doc.get("clasificacion_llm", {}).get("clasificaciones", []):
            cluster_id = clasif.get("cluster_id")
            categoria_nombre = (
                clasif.get("concepto") or clasif.get("categoria") or "Sin Nombre"
            )
            if cluster_id is None:
                continue

            node_cat_id = f"NODO_CAT_CLUSTER_{cluster_id}"
            if not self.G.has_node(node_cat_id):
                self.G.add_node(
                    node_cat_id,
                    label=categoria_nombre,
                    tipo="NODO_CATEGORIA",
                    nivel=1,
                    cluster_id=cluster_id,
                )
                self.G.add_edge(settings.ROOT_ID, node_cat_id, relacion="CONTIENE_CATEGORIA")

            self.G.add_edge(
                node_cat_id,
                subnodo_doc_id,
                relacion="AGRUPA_DOCUMENTO",
                confianza=clasif.get("confianza"),
            )

        for seccion_idx, sec in enumerate(doc.get("secciones", [])):
            subnodo_sec_id = f"SUBNODO_SEC_{document_id}_{seccion_idx}"
            entidades = sec.get("entidades", [])

            self.G.add_node(
                subnodo_sec_id,
                label=sec.get("titulo", f"Sección {seccion_idx + 1}"),
                tipo="SUBNODO_SECCION",
                nivel=3,
                document_id=document_id,
                documento_nombre=documento_nombre,
                seccion_idx=seccion_idx,
                ruta_jerarquica=sec.get("ruta_jerarquica", []),
                chunk_texto=sec.get("texto")
                or ", ".join(
                    e.get("canonical", "")
                    for e in entidades
                    if es_texto_valido(e.get("canonical", ""))
                ),
            )
            self.G.add_edge(subnodo_sec_id, subnodo_doc_id, relacion="PERTENECE_A_DOCUMENTO")

            for e in entidades:
                canonical = e.get("canonical", "").strip()
                if canonical and es_texto_valido(canonical):
                    entity_id = f"ENT_{normalizar_key(canonical)}"
                    if not self.G.has_node(entity_id):
                        self.G.add_node(
                            entity_id,
                            label=canonical,
                            tipo=f"NODO_ENTIDAD_{e.get('tipo', 'DESCONOCIDO')}",
                            nivel=4,
                            embedding_id=entity_id,
                        )

                    self.G.add_edge(
                        subnodo_sec_id,
                        entity_id,
                        relacion="MENCIONA_ENTIDAD",
                        document_id=document_id,
                        documento_nombre=documento_nombre,
                        seccion_idx=seccion_idx,
                        origen_extraccion=e.get("origen"),
                    )

            top_conceptos = sorted(
                sec.get("conceptos", []), key=lambda c: c.get("score", 0), reverse=True
            )[:settings.CONCEPTOS_TOP_POR_SECCION]

            for c in top_conceptos:
                score = c.get("score", 0)
                concepto_val = c.get("concepto", "").strip()
                if (
                    score >= settings.SCORE_MINIMO_CONCEPTO
                    and concepto_val
                    and es_texto_valido(concepto_val)
                ):
                    nodo_concepto_id = f"CONCEPTO_{normalizar_key(concepto_val)}"
                    if not self.G.has_node(nodo_concepto_id):
                        self.G.add_node(
                            nodo_concepto_id,
                            label=concepto_val,
                            tipo="NODO_CONCEPTO",
                            nivel=4,
                            score_yake=score,
                        )

                    self.G.add_edge(
                        subnodo_sec_id,
                        nodo_concepto_id,
                        relacion="DEFINE_CONCEPTO",
                        document_id=document_id,
                        documento_nombre=documento_nombre,
                        seccion_idx=seccion_idx,
                        score=score,
                    )

            mapa_entidades_seccion = self.construir_mapa_entidades_seccion(entidades)
            for rel in sec.get("relaciones", []):
                confianza = rel.get("confianza")
                if confianza is not None and confianza < settings.CONFIANZA_MINIMA_RELACION:
                    continue

                sujeto_txt = rel.get("sujeto", "").strip()
                objeto_txt = rel.get("objeto", "").strip()
                if not es_texto_valido(sujeto_txt) or not es_texto_valido(objeto_txt):
                    continue

                entity_id_sujeto = f"ENT_{normalizar_key(mapa_entidades_seccion.get(normalizar_key(sujeto_txt), sujeto_txt))}"
                entity_id_objeto = f"ENT_{normalizar_key(mapa_entidades_seccion.get(normalizar_key(objeto_txt), objeto_txt))}"

                for eid, label in [
                    (entity_id_sujeto, sujeto_txt),
                    (entity_id_objeto, objeto_txt),
                ]:
                    if not self.G.has_node(eid):
                        self.G.add_node(
                            eid,
                            label=label,
                            tipo="NODO_ENTIDAD_SIN_RESOLVER",
                            nivel=4,
                            embedding_id=eid,
                        )

                self.G.add_edge(
                    entity_id_sujeto,
                    entity_id_objeto,
                    relacion=rel.get("relacion", rel.get("verbo", "RELACIONADO_CON")),
                    tipo_relacion=rel.get("tipo_relacion", "DESCONOCIDA"),
                    document_id=document_id,
                    documento_nombre=documento_nombre,
                    seccion_idx=seccion_idx,
                    contexto=rel.get("contexto", ""),
                    confianza=confianza,
                    origen_extraccion=rel.get("origen", "desconocido"),
                )

    def generar_y_guardar_embeddings(self, entidades_nuevas: dict[str, str]) -> None:
        if not entidades_nuevas:
            return
        vectores = self.modelo_embeddings.encode(
            list(entidades_nuevas.values()),
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        for eid, vector in zip(entidades_nuevas.keys(), vectores):
            self.embeddings_store[eid] = vector.tolist()
        logger.info("Generados %d embeddings nuevos.", len(entidades_nuevas))