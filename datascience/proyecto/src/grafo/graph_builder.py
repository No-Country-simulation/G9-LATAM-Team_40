from __future__ import annotations

import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer

from settings import settings
# Se asume que filtros provee estas utilidades; puedes ajustarlo a tu entorno.
from .filtros import es_texto_valido, normalizar_key, limpiar_label

logger = logging.getLogger("GraphRAGBuilder")

class GraphRAGBuilder:
    def __init__(self, ruta_grafo: Path, ruta_embeddings: Path):
        self.ruta_grafo = ruta_grafo
        self.ruta_embeddings = ruta_embeddings
        self.modelo_embeddings = SentenceTransformer(settings.MODELO_EMBEDDINGS)
        
        # Estructuras de datos para el Grafo de Conocimiento Global
        self.categorias: dict[str, dict] = {}
        self.documentos: dict[str, dict] = {}
        self.secciones: dict[str, dict] = {}
        self.nodos: dict[str, dict] = {}        # Entidades y Conceptos
        self.relaciones: dict[str, dict] = {}   # Relaciones extraídas y estructurales
        self.rutas: list[dict] = []             # Rutas precalculadas (opcional)
        
        self.embeddings_store = self._cargar_store_embeddings()
        self._cargar_grafo_existente()

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
            json.dumps(self.embeddings_store, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _cargar_grafo_existente(self) -> None:
        """Carga el estado del grafo desde el JSON si ya existe, respetando la nueva estructura."""
        if self.ruta_grafo.exists():
            try:
                data = json.loads(self.ruta_grafo.read_text(encoding="utf-8"))
                grafo = data.get("grafo_conocimiento", {})
                self.categorias = {c["id"]: c for c in grafo.get("categorias", [])}
                self.documentos = {d["id"]: d for d in grafo.get("documentos", [])}
                self.secciones = {s["id"]: s for s in grafo.get("secciones", [])}
                self.nodos = {n["id"]: n for n in grafo.get("nodos", [])}
                self.relaciones = {r["id"]: r for r in grafo.get("relaciones", [])}
                self.rutas = grafo.get("rutas", [])
            except Exception as e:
                logger.error("Error al cargar el grafo existente: %s. Empezando de cero.", e)

    def guardar_grafo(self) -> None:
        """Exporta el grafo estructurado exactamente como se solicita."""
        self._generar_relaciones_entre_documentos()
        
        grafo_json = {
            "grafo_conocimiento": {
                "categorias": list(self.categorias.values()),
                "documentos": list(self.documentos.values()),
                "secciones": list(self.secciones.values()),
                "nodos": list(self.nodos.values()),
                "relaciones": list(self.relaciones.values()),
                "rutas": self.rutas
            }
        }
        
        self.ruta_grafo.parent.mkdir(parents=True, exist_ok=True)
        self.ruta_grafo.write_text(
            json.dumps(grafo_json, ensure_ascii=False, indent=2), 
            encoding="utf-8"
        )

    def _generar_id_hash(self, base_string: str, prefijo: str = "REL") -> str:
        """Genera un identificador determinístico basado en el contenido."""
        hash_obj = hashlib.md5(base_string.encode("utf-8")).hexdigest()
        return f"{prefijo}_{hash_obj[:12]}"

    def procesar_documento(self, doc: dict) -> None:
        doc_original_id = doc.get("documento_id", "unknown")
        doc_nombre = doc.get("documento_nombre", "Sin Nombre")
        doc_id = f"DOC_{normalizar_key(doc_original_id)}"
        
        # 1. Procesar Documento
        self.documentos[doc_id] = {
            "id": doc_id,
            "tipo": "DOCUMENTO",
            "documento_id": doc_original_id,
            "nombre": doc_nombre,
            "metadata": doc.get("metadata", {}),
            "clasificacion_llm": doc.get("clasificacion_llm", {})
        }

        # 2. Procesar Categorías y relacionar con el Documento
        clasificacion_llm = doc.get("clasificacion_llm", {})
        clasificaciones = clasificacion_llm.get("clasificaciones", [])
        
        for clasif in clasificaciones:
            categoria_nombre = clasif.get("categoria", "General")
            cat_id = f"CAT_{normalizar_key(categoria_nombre)}"
            
            if cat_id not in self.categorias:
                self.categorias[cat_id] = {
                    "id": cat_id,
                    "tipo": "CATEGORIA",
                    "nombre": categoria_nombre,
                    "confianza": clasif.get("confianza", 1.0)
                }
            
            # Relación: CATEGORIA -> CLASIFICA -> DOCUMENTO
            rel_cat_doc_id = self._generar_id_hash(f"{cat_id}_CLASIFICA_{doc_id}")
            self.relaciones[rel_cat_doc_id] = {
                "id": rel_cat_doc_id,
                "sujeto_id": cat_id,
                "tipo": "CLASIFICA",
                "objeto_id": doc_id
            }

        # 3. Procesar Secciones, Entidades, Conceptos y Relaciones
        secciones = doc.get("secciones", [])
        for idx, sec in enumerate(secciones):
            sec_titulo = sec.get("titulo", f"Seccion {idx}")
            sec_id = f"SEC_{normalizar_key(doc_original_id)}_{idx}"
            ruta_jerarquica = sec.get("ruta_jerarquica", [])
            
            # Nodo de Sección
            self.secciones[sec_id] = {
                "id": sec_id,
                "tipo": "SECCION",
                "documento_id": doc_original_id,
                "documento_nombre": doc_nombre,
                "titulo": sec_titulo,
                "nivel": sec.get("nivel", 1),
                "ruta_jerarquica": ruta_jerarquica
            }

            # Relación estructural: DOCUMENTO -> CONTIENE -> SECCION
            rel_doc_sec_id = self._generar_id_hash(f"{doc_id}_CONTIENE_{sec_id}")
            self.relaciones[rel_doc_sec_id] = {
                "id": rel_doc_sec_id,
                "sujeto_id": doc_id,
                "tipo": "CONTIENE",
                "objeto_id": sec_id
            }

            # Procesar Entidades
            for ent in sec.get("entidades", []):
                canonical = ent.get("canonical") or ent.get("texto")
                if not canonical or not es_texto_valido(canonical):
                    continue
                
                ent_id = f"ENT_{normalizar_key(canonical)}"
                self._registrar_nodo_semantico(
                    nodo_id=ent_id,
                    tipo="ENTIDAD",
                    nombre=canonical,
                    subtipo=ent.get("tipo", "DESCONOCIDO"),
                    doc_id=doc_id,
                    doc_original_id=doc_original_id,
                    doc_nombre=doc_nombre,
                    sec_id=sec_id,
                    sec_titulo=sec_titulo,
                    ruta_jerarquica=ruta_jerarquica,
                    origen=ent.get("origen", "llm")
                )

            # Procesar Conceptos
            for con in sec.get("conceptos", []):
                concepto_texto = con.get("concepto")
                if not concepto_texto or not es_texto_valido(concepto_texto):
                    continue
                
                con_id = f"CON_{normalizar_key(concepto_texto)}"
                self._registrar_nodo_semantico(
                    nodo_id=con_id,
                    tipo="CONCEPTO",
                    nombre=concepto_texto,
                    score=con.get("score", 0.0),
                    doc_id=doc_id,
                    doc_original_id=doc_original_id,
                    doc_nombre=doc_nombre,
                    sec_id=sec_id,
                    sec_titulo=sec_titulo,
                    ruta_jerarquica=ruta_jerarquica,
                    origen="llm"
                )

            # Procesar Relaciones Semánticas (sujeto -> verbo -> objeto)
            for rel in sec.get("relaciones", []):
                sujeto_norm = normalizar_key(rel.get("sujeto", ""))
                objeto_norm = normalizar_key(rel.get("objeto", ""))
                tipo_relacion = rel.get("relacion", "RELACIONADO_CON")
                
                # Asumimos que los IDs de sujeto y objeto ya existen como ENT_ o CON_
                # Para mayor robustez, se busca en los nodos, pero generamos el prefijo base ENT_ asumiendo entidades
                sujeto_id = f"ENT_{sujeto_norm}" if f"ENT_{sujeto_norm}" in self.nodos else f"CON_{sujeto_norm}"
                objeto_id = f"ENT_{objeto_norm}" if f"ENT_{objeto_norm}" in self.nodos else f"CON_{objeto_norm}"
                
                # Si por error de extracción el LLM inventó un término que no está en la lista de entidades,
                # lo ignoramos o forzamos su creación (aquí forzamos creación rápida como concepto por seguridad)
                if sujeto_id not in self.nodos: sujeto_id = f"CON_{sujeto_norm}"
                if objeto_id not in self.nodos: objeto_id = f"CON_{objeto_norm}"

                rel_sem_id = self._generar_id_hash(f"{sujeto_id}_{tipo_relacion}_{objeto_id}_{doc_id}_{sec_id}", "REL")
                
                self.relaciones[rel_sem_id] = {
                    "id": rel_sem_id,
                    "sujeto_id": sujeto_id,
                    "tipo": tipo_relacion,
                    "objeto_id": objeto_id,
                    "trazabilidad": {
                        "documento_id": doc_original_id,
                        "documento_nombre": doc_nombre,
                        "seccion_id": sec_id,
                        "titulo_seccion": sec_titulo,
                        "ruta_jerarquica": ruta_jerarquica,
                        "contexto": rel.get("contexto", ""),
                        "origen": rel.get("origen", "llm"),
                        "confianza": rel.get("confianza", 1.0)
                    }
                }

    def _registrar_nodo_semantico(self, nodo_id: str, tipo: str, nombre: str, doc_id: str, 
                                  doc_original_id: str, doc_nombre: str, sec_id: str, 
                                  sec_titulo: str, ruta_jerarquica: list, origen: str, 
                                  subtipo: str = None, score: float = None):
        """Agrega un nodo global (Entidad/Concepto) y centraliza sus apariciones para trazabilidad."""
        if nodo_id not in self.nodos:
            self.nodos[nodo_id] = {
                "id": nodo_id,
                "tipo": tipo,
                "nombre": nombre,
                "apariciones": []
            }
            if subtipo: self.nodos[nodo_id]["subtipo"] = subtipo
            if score: self.nodos[nodo_id]["score"] = score

        aparicion = {
            "documento_id": doc_original_id,
            "documento_nombre": doc_nombre,
            "seccion_id": sec_id,
            "titulo_seccion": sec_titulo,
            "ruta_jerarquica": ruta_jerarquica,
            "origen": origen
        }
        
        # Evitar duplicar la misma aparición si el concepto se extrae varias veces en la misma sección
        if aparicion not in self.nodos[nodo_id]["apariciones"]:
            self.nodos[nodo_id]["apariciones"].append(aparicion)

    def _generar_relaciones_entre_documentos(self) -> None:
        """Infere y crea relaciones entre documentos que comparten las mismas entidades."""
        # Agrupar documentos por entidad
        for nodo_id, nodo_data in self.nodos.items():
            docs_asociados = list({ap["documento_id"] for ap in nodo_data.get("apariciones", [])})
            
            # Si una entidad aparece en 2 o más documentos distintos
            if len(docs_asociados) > 1:
                for i in range(len(docs_asociados)):
                    for j in range(i + 1, len(docs_asociados)):
                        doc_1 = f"DOC_{normalizar_key(docs_asociados[i])}"
                        doc_2 = f"DOC_{normalizar_key(docs_asociados[j])}"
                        
                        rel_id = self._generar_id_hash(f"{doc_1}_COMPARTE_{doc_2}_{nodo_id}", "REL_DOC")
                        if rel_id not in self.relaciones:
                            self.relaciones[rel_id] = {
                                "id": rel_id,
                                "sujeto_id": doc_1,
                                "tipo": "COMPARTE_ENTIDAD",
                                "objeto_id": doc_2,
                                "evidencia": {
                                    "nodo_compartido": nodo_id
                                }
                            }

    def recolectar_nodos_sin_embedding(self) -> dict[str, str]:
        """Identifica qué Categorías, Entidades o Conceptos aún no tienen vector generado."""
        pendientes = {}
        # También incrustamos Categorías para búsquedas top-level
        for cat_id, data in self.categorias.items():
            if cat_id not in self.embeddings_store:
                pendientes[cat_id] = data["nombre"]
                
        for nodo_id, data in self.nodos.items():
            if nodo_id not in self.embeddings_store:
                pendientes[nodo_id] = data["nombre"]
                
        return pendientes

    def generar_y_guardar_embeddings(self) -> None:
        """Genera los vectores sólo para los nodos semánticos que falten."""
        nodos_pendientes = self.recolectar_nodos_sin_embedding()
        if not nodos_pendientes:
            logger.info("No hay nodos nuevos para generar embeddings.")
            return
            
        textos = list(nodos_pendientes.values())
        ids = list(nodos_pendientes.keys())
        
        logger.info(f"Generando {len(textos)} embeddings nuevos...")
        vectores = self.modelo_embeddings.encode(
            textos,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        
        for eid, vector in zip(ids, vectores):
            self.embeddings_store[eid] = vector.tolist()
            
        self.guardar_store_embeddings()
        logger.info("Embeddings guardados exitosamente.")