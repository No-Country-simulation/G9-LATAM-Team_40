"""Carga índices GraphRAG base o privados y resuelve secciones bajo demanda."""
from __future__ import annotations

import difflib
import json
import logging
import re
from pathlib import Path
from uuid import UUID

from settings import Settings, settings
from storage.oci_object_storage import ObjectNotFoundError, fetch_document_on_demand

logger = logging.getLogger("IndiceGrafo")

UMBRAL_SIMILITUD_TITULO_FUZZY = 0.72
_PATRON_RUIDO_MARKDOWN = re.compile(r"[*#_`>]+")
_PATRON_ESPACIOS = re.compile(r"\s+")


def _normalizar_titulo(texto: str) -> str:
    if not texto:
        return ""
    limpio = _PATRON_RUIDO_MARKDOWN.sub(" ", texto)
    return _PATRON_ESPACIOS.sub(" ", limpio).strip().lower()


class IndiceGrafo:
    DOMINIO_A_CARPETA = {"Leyes": "LEYES", "ISOs": "ISOS"}
    SUFIJO_ARCHIVO_SECCIONES = ".secciones.json"

    def __init__(self, config: Settings = settings):
        self.settings = config
        self.nivel_1_categorias: dict[str, dict] = {}
        self.nivel_2_subcategorias: dict[str, dict] = {}
        self.nivel_3_relaciones: dict[str, dict] = {}
        self._cache_documentos: dict[str, dict | None] = {}
        self._cache_markdown: dict[Path, str] = {}
        self._manifest = self._cargar_manifest()
        self._cargar_grafo()
        self.embeddings_store = self._cargar_embeddings()
        self._clasificaciones_por_documento = self._cargar_clasificaciones()
        logger.info(
            "IndiceGrafo inicializado: N1=%d, N2=%d, N3=%d, embeddings=%d, documentos=%d",
            len(self.nivel_1_categorias), len(self.nivel_2_subcategorias),
            len(self.nivel_3_relaciones), len(self.embeddings_store),
            len(self._clasificaciones_por_documento),
        )

    def _cargar_manifest(self) -> dict[str, dict]:
        ruta = self.settings.JSON_INPUT_DIR / "document_manifest.json"
        if not ruta.exists():
            return {}
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            documentos = data.get("documents", data.get("documentos", data)) if isinstance(data, dict) else data
            if isinstance(documentos, list):
                return {
                    str(item.get("documento_id")): item
                    for item in documentos
                    if isinstance(item, dict) and item.get("documento_id")
                }
            if isinstance(documentos, dict):
                return {str(key): value for key, value in documentos.items() if isinstance(value, dict)}
        except Exception as exc:
            logger.warning("No se pudo leer document_manifest.json: %s", exc)
        return {}

    def _cargar_grafo(self) -> None:
        ruta = self.settings.FILE_GRAFO_JSON
        if not ruta.exists():
            return
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            grafo = data.get("grafo_conceptual", {})
            self.nivel_1_categorias = {n["id"]: n for n in grafo.get("nivel_1_categorias", [])}
            self.nivel_2_subcategorias = {n["id"]: n for n in grafo.get("nivel_2_subcategorias", [])}
            self.nivel_3_relaciones = {n["id"]: n for n in grafo.get("nivel_3_relaciones", [])}
        except Exception as exc:
            logger.error("Error al cargar el grafo JSON: %s", exc)

    def _cargar_embeddings(self) -> dict:
        ruta = self.settings.FILE_EMBEDDINGS_JSON
        if not ruta.exists():
            return {}
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.error("Error al cargar embeddings JSON: %s", exc)
            return {}

    def _cargar_clasificaciones(self) -> dict[str, dict]:
        resultado: dict[str, dict] = {}
        for ruta in (self.settings.FILE_ISO_CLASIFICADO, self.settings.FILE_LEYES_CLASIFICADO):
            if not ruta.exists():
                continue
            try:
                data = json.loads(ruta.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Error al leer clasificación %s: %s", ruta, exc)
                continue
            for doc in data if isinstance(data, list) else [data]:
                documento_id = doc.get("documento_id")
                clasificaciones = doc.get("clasificaciones") or []
                if not documento_id:
                    continue
                if not clasificaciones:
                    resultado[str(documento_id)] = {"categoria": "Sin categoría", "palabras_clave": []}
                    continue
                mejor = max(clasificaciones, key=lambda item: item.get("confianza", 0.0))
                resultado[str(documento_id)] = {
                    "categoria": str(mejor.get("categoria") or "Sin categoría").strip(),
                    "palabras_clave": list(mejor.get("palabras_claves") or []),
                }
        return resultado

    @classmethod
    def _carpeta_a_dominio(cls, carpeta: str) -> str:
        for dominio, categoria in cls.DOMINIO_A_CARPETA.items():
            if categoria == carpeta:
                return dominio
        return carpeta

    def _resolver_documento_lazy(self, documento_id: str) -> dict | None:
        if documento_id in self._cache_documentos:
            return self._cache_documentos[documento_id]
        for ruta_cat in self.settings.RUTAS_CATEGORIAS:
            carpeta = ruta_cat["categoria"]
            output_dir = ruta_cat["output_dir"]
            dominio = self._carpeta_a_dominio(carpeta)
            local_path = output_dir / f"{documento_id}{self.SUFIJO_ARCHIVO_SECCIONES}"
            if not local_path.exists() and self.settings.DATA_SOURCE.lower() == "oci":
                try:
                    fetch_document_on_demand(self.settings, local_path)
                except ObjectNotFoundError:
                    continue
                except Exception as exc:
                    logger.warning("No se pudo descargar %s: %s", documento_id, exc)
                    continue
            if not local_path.exists():
                continue
            try:
                doc = json.loads(local_path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Error leyendo %s: %s", local_path, exc)
                continue
            manifest = self._manifest.get(str(documento_id), {})
            result = {
                "dominio": manifest.get("dominio", dominio),
                "secciones": doc.get("secciones", []),
                "titulo": str(manifest.get("nombre_original") or doc.get("titulo") or "").strip(),
                "source_path": doc.get("source_path", ""),
                "archivo_id": manifest.get("archivo_id"),
            }
            self._cache_documentos[documento_id] = result
            return result
        self._cache_documentos[documento_id] = None
        return None

    def _ruta_markdown(self, documento_id: str, dominio: str) -> Path | None:
        carpeta = self.DOMINIO_A_CARPETA.get(dominio, dominio.upper())
        directorio = self.settings.ARCHIVOS_DIR / carpeta / "md"
        exacta = directorio / f"{documento_id}.md"
        if exacta.exists():
            return exacta
        if directorio.exists():
            objetivo = exacta.name.lower()
            return next((path for path in directorio.glob("*.md") if path.name.lower() == objetivo), None)
        return None

    def _leer_markdown(self, ruta: Path) -> str:
        if ruta not in self._cache_markdown:
            try:
                self._cache_markdown[ruta] = ruta.read_text(encoding="utf-8")
            except Exception:
                self._cache_markdown[ruta] = ""
        return self._cache_markdown[ruta]

    def _extraer_contenido_desde_markdown(self, documento_id: str, dominio: str, titulo_seccion: str) -> str:
        ruta = self._ruta_markdown(documento_id, dominio)
        if not ruta or not titulo_seccion:
            return ""
        texto = self._leer_markdown(ruta)
        inicio = texto.find(titulo_seccion)
        if inicio < 0:
            return ""
        fin = texto.find("\n\n", inicio + len(titulo_seccion))
        return texto[inicio:] if fin < 0 else texto[inicio:fin].strip()

    def resolver_nodos_seccion_desde_nodo(self, nodo_id: str) -> list[dict]:
        if nodo_id in self.nivel_3_relaciones:
            parent = self.nivel_3_relaciones[nodo_id].get("parent_id")
            return [self.nivel_2_subcategorias[parent]] if parent in self.nivel_2_subcategorias else []
        if nodo_id in self.nivel_2_subcategorias:
            return [self.nivel_2_subcategorias[nodo_id]]
        if nodo_id in self.nivel_1_categorias:
            return [n for n in self.nivel_2_subcategorias.values() if n.get("parent_id") == nodo_id]
        return []

    def resolver_contenido_nodo_seccion(self, nodo_sec: dict) -> list[dict]:
        resultados = []
        for ref in nodo_sec.get("secciones", []):
            documento_id = str(ref.get("documento_id", "")).strip()
            titulo = str(ref.get("titulo", "")).strip()
            result = self.resolver_contenido_por_documento_y_titulo(documento_id, titulo)
            if result:
                resultados.append({"documento_id": documento_id, "titulo_seccion": titulo, **result})
        return resultados

    def resolver_contenido_por_documento_y_titulo(self, documento_id: str, titulo_seccion: str) -> dict | None:
        fuente = self._resolver_documento_lazy(documento_id)
        if not fuente:
            return None
        secciones = fuente["secciones"]
        exactas = [s for s in secciones if str(s.get("titulo", "")).strip() == titulo_seccion.strip()]
        sec = exactas[0] if exactas else None
        if sec is None:
            normalizado = _normalizar_titulo(titulo_seccion)
            normalizadas = [s for s in secciones if _normalizar_titulo(str(s.get("titulo", ""))) == normalizado]
            sec = normalizadas[0] if normalizadas else None
        if sec is None:
            disponibles = {_normalizar_titulo(str(s.get("titulo", ""))): s for s in secciones}
            matches = difflib.get_close_matches(_normalizar_titulo(titulo_seccion), disponibles, n=1, cutoff=UMBRAL_SIMILITUD_TITULO_FUZZY)
            sec = disponibles[matches[0]] if matches else None
        if sec is None:
            return None
        texto = sec.get("texto") or sec.get("contenido") or sec.get("texto_seccion")
        if not texto:
            texto = self._extraer_contenido_desde_markdown(documento_id, fuente["dominio"], titulo_seccion)
        texto = str(texto or titulo_seccion).strip()
        if len(texto) > self.settings.MAX_CARACTERES_CONTENIDO_SECCION:
            texto = texto[:self.settings.MAX_CARACTERES_CONTENIDO_SECCION].rstrip() + "…"
        return {
            "texto": texto,
            "dominio": fuente["dominio"],
            "nivel": sec.get("nivel") or 1,
            "ruta_jerarquica": sec.get("ruta_jerarquica", []),
            "source_path": fuente.get("source_path", ""),
            "archivo_id": fuente.get("archivo_id"),
        }

    def obtener_info_documento(self, documento_id: str) -> dict:
        fuente = self._resolver_documento_lazy(str(documento_id))
        return {
            "dominio": fuente["dominio"],
            "titulo": fuente["titulo"],
            "source_path": fuente.get("source_path", ""),
            "archivo_id": fuente.get("archivo_id"),
        } if fuente else {}

    def obtener_categoria_y_palabras_clave(self, documento_id: str) -> dict:
        return self._clasificaciones_por_documento.get(
            str(documento_id), {"categoria": "Sin categoría", "palabras_clave": []}
        )
