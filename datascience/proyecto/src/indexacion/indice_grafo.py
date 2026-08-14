import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# ------------------------------------------------------------------------------
# IMPORTACIÓN DE CONFIGURACIÓN CENTRALIZADA
# ------------------------------------------------------------------------------
from settings import settings

logger = logging.getLogger("IndiceGrafo")


class IndiceGrafo:
    """
    Carga el grafo de conocimiento y construye índices inversos en memoria
    para realizar búsquedas por aristas salientes y entrantes en O(1).
    """

    def __init__(self, 
        grafo_json_path: Path | None = None, 
        embeddings_json_path: Path | None = None):
        self.grafo_json_path = grafo_json_path or settings.FILE_GRAFO_JSON
        self.embeddings_json_path = embeddings_json_path or settings.FILE_EMBEDDINGS_JSON

        if not self.grafo_json_path.exists():
            raise FileNotFoundError(f"No existe el archivo de grafo en: {self.grafo_json_path}")

        logger.info("Cargando estructura del grafo desde %s...", self.grafo_json_path)
        data = json.loads(self.grafo_json_path.read_text(encoding="utf-8"))

        nodos_raw = data.get("nodos", data.get("nodes", []))
        self.nodos: Dict[str, Dict[str, Any]] = {
            str(n.get("id") or n.get("nombre")): n for n in nodos_raw
        }

        self.aristas_salientes: Dict[str, List[Dict[str, Any]]] = {}
        self.aristas_entrantes: Dict[str, List[Dict[str, Any]]] = {}

        aristas_raw = data.get("aristas", data.get("edges", []))
        for a in aristas_raw:
            origen = str(a.get("origen"))
            destino = str(a.get("destino"))
            self.aristas_salientes.setdefault(origen, []).append(a)
            self.aristas_entrantes.setdefault(destino, []).append(a)

        self.embeddings_store: Dict[str, List[float]] = {}
        if embeddings_json_path.exists():
            self.embeddings_store = json.loads(embeddings_json_path.read_text(encoding="utf-8"))

        logger.info(
            "IndiceGrafo listo: %d nodos | %d aristas | %d embeddings",
            len(self.nodos),
            len(aristas_raw),
            len(self.embeddings_store),
        )

    def obtener_documentos_de_categoria(self, node_cat_id: str, tope: int = 10) -> List[str]:
        """Devuelve los IDs de los documentos asociados a una categoría."""
        docs = [
            str(a["destino"])
            for a in self.aristas_salientes.get(node_cat_id, [])
            if a.get("relacion") == "AGRUPA_DOCUMENTO"
        ]
        return docs[:tope]

    def obtener_secciones_de_documento(self, subnodo_doc_id: str) -> List[str]:
        """Devuelve las secciones vinculadas a un documento específico."""
        return [
            str(a["origen"])
            for a in self.aristas_entrantes.get(subnodo_doc_id, [])
            if a.get("relacion") == "PERTENECE_A_DOCUMENTO"
        ]