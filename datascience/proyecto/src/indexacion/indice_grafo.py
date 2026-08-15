"""
Módulo para cargar el Grafo JSON, el Store de Embeddings y el contenido fuente
de las secciones (para resolución directa por índice, sin re-embeber por consulta).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

# Se asume que settings está disponible e importado correctamente en tu entorno
from settings import settings

logger = logging.getLogger("IndiceGrafo")


class IndiceGrafo:
    """Carga y mantiene en memoria el Grafo JSON, los Embeddings y el contenido fuente."""

    DOMINIO_A_CARPETA = {
        "Leyes": "LEYES",
        "ISOs": "ISOS",
    }

    def __init__(self):
        self.categorias: dict[str, dict] = {}
        self.documentos: dict[str, dict] = {}
        self.secciones: dict[str, dict] = {}
        self.nodos: dict[str, dict] = {}
        self.relaciones: dict[str, dict] = {}

        self._cargar_grafo()
        self.embeddings_store = self._cargar_embeddings()

        # documento_id (original, sin normalizar) -> {"dominio": str, "secciones": [dict,...]}
        self.fuente_documentos: dict[str, dict] = {}
        self._cache_markdown: dict[Path, str] = {}
        self._cargar_fuente_documentos()

        logger.info(
            "IndiceGrafo inicializado: %d nodos semánticos, %d embeddings, %d documentos fuente.",
            len(self.nodos), len(self.embeddings_store), len(self.fuente_documentos)
        )

    # -------------------------------------------------------------------------
    # MÉTODOS DE CARGA E INICIALIZACIÓN
    # -------------------------------------------------------------------------

    def _cargar_grafo(self) -> None:
        """Carga los nodos, relaciones y metadata desde el archivo de grafo principal."""
        if not settings.FILE_GRAFO_JSON.exists():
            logger.warning("El archivo de grafo no existe en: %s", settings.FILE_GRAFO_JSON)
            return
        
        try:
            data = json.loads(settings.FILE_GRAFO_JSON.read_text(encoding="utf-8"))
            grafo = data.get("grafo_conocimiento", {})
            self.categorias = {c["id"]: c for c in grafo.get("categorias", [])}
            self.documentos = {d["id"]: d for d in grafo.get("documentos", [])}
            self.secciones = {s["id"]: s for s in grafo.get("secciones", [])}
            self.nodos = {n["id"]: n for n in grafo.get("nodos", [])}
            self.relaciones = {r["id"]: r for r in grafo.get("relaciones", [])}
            logger.info("Grafo cargado exitosamente. Documentos mapeados: %d", len(self.documentos))
        except Exception as e:
            logger.error("Error al cargar el grafo JSON: %s", e)

    def _cargar_embeddings(self) -> dict:
        """Carga el almacén de vectores JSON en memoria."""
        if not settings.FILE_EMBEDDINGS_JSON.exists():
            logger.warning("El archivo de embeddings no existe en: %s", settings.FILE_EMBEDDINGS_JSON)
            return {}
        
        try:
            embeddings = json.loads(settings.FILE_EMBEDDINGS_JSON.read_text(encoding="utf-8"))
            logger.info("Store de embeddings cargado: %d vectores.", len(embeddings))
            return embeddings
        except Exception as e:
            logger.error("Error al cargar embeddings JSON: %s", e)
            return {}

    def _cargar_fuente_documentos(self) -> None:
        """
        Carga UNA SOLA VEZ (al iniciar el pipeline) el contenido crudo de las secciones
        desde los JSON clasificados, indexado por documento_id + posición.
        Esto elimina la necesidad de releer/filtrar/re-embeber archivos en cada consulta:
        la Etapa 4 solo hace lookup directo por (documento_id, idx) derivado del seccion_id.
        """
        rutas = [
            (settings.FILE_LEYES_CLASIFICADO, "Leyes"),
            (settings.FILE_ISO_CLASIFICADO, "ISOs"),
        ]
        
        for ruta_json, dominio in rutas:
            if not ruta_json.exists():
                logger.warning("Archivo fuente no encontrado (%s): %s", dominio, ruta_json)
                continue
            
            try:
                datos = json.loads(ruta_json.read_text(encoding="utf-8"))
                documentos = datos if isinstance(datos, list) else datos.get("documentos", [])
                
                for doc in documentos:
                    doc_id = str(doc.get("documento_id") or doc.get("documento_nombre") or "")
                    if not doc_id:
                        continue
                        
                    self.fuente_documentos[doc_id] = {
                        "dominio": dominio,
                        "secciones": doc.get("secciones", []),
                    }
            except Exception as e:
                logger.error("Error leyendo archivo fuente %s: %s", ruta_json, e)

    # -------------------------------------------------------------------------
    # HELPERS DE EXTRACCIÓN MARKDOWN
    # -------------------------------------------------------------------------

    def _ruta_markdown(self, documento_nombre: str, dominio: str) -> Path | None:
        """Localiza el archivo .md original a partir del dominio y el nombre de documento."""
        carpeta = self.DOMINIO_A_CARPETA.get(dominio)
        if not carpeta:
            logger.warning("Dominio desconocido para resolución de Markdown: %s", dominio)
            return None

        nombre = documento_nombre if documento_nombre.lower().endswith(".md") else f"{documento_nombre}.md"
        ruta = settings.ARCHIVOS_DIR / carpeta / "md" / nombre
        if ruta.exists():
            return ruta

        # Fallback tolerante: busca por coincidencia de nombre sin distinguir mayúsculas/espacios extra.
        directorio = settings.ARCHIVOS_DIR / carpeta / "md"
        if directorio.exists():
            objetivo = nombre.strip().lower()
            for candidato in directorio.glob("*.md"):
                if candidato.name.strip().lower() == objetivo:
                    return candidato

        logger.warning("No se encontró el archivo Markdown para '%s' en %s", nombre, directorio)
        return None

    def _leer_markdown(self, ruta: Path) -> str:
        """Lee y cachea el contenido completo de un .md (una sola vez por documento)."""
        if ruta in self._cache_markdown:
            return self._cache_markdown[ruta]
        
        try:
            texto = ruta.read_text(encoding="utf-8")
        except Exception as e:
            logger.error("Error leyendo Markdown %s: %s", ruta, e)
            texto = ""
            
        self._cache_markdown[ruta] = texto
        return texto

    def _extraer_contenido_desde_markdown(
        self,
        documento_nombre: str,
        dominio: str,
        titulo_actual: str,
        secciones_raw: list[dict],
        idx: int,
    ) -> str:
        """
        Va al Markdown original, localiza el título de la sección actual y extrae
        todo el texto hasta la aparición del título de la siguiente sección
        (o hasta el final del documento si es la última).
        """
        if not titulo_actual:
            return ""

        ruta_md = self._ruta_markdown(documento_nombre, dominio)
        if not ruta_md:
            return ""

        texto_md = self._leer_markdown(ruta_md)
        if not texto_md:
            return ""

        pos_inicio = texto_md.find(titulo_actual)
        if pos_inicio == -1:
            logger.warning(
                "Título no encontrado en el Markdown: '%s...' (archivo: %s)",
                titulo_actual[:60], ruta_md.name
            )
            return ""

        pos_fin = len(texto_md)
        siguiente_idx = idx + 1
        
        while siguiente_idx < len(secciones_raw):
            titulo_siguiente = str(secciones_raw[siguiente_idx].get("titulo", "")).strip()
            if titulo_siguiente:
                candidato = texto_md.find(titulo_siguiente, pos_inicio + len(titulo_actual))
                if candidato != -1:
                    pos_fin = candidato
                    break
            siguiente_idx += 1

        contenido = texto_md[pos_inicio:pos_fin].strip()
        limite = settings.MAX_CARACTERES_CONTENIDO_SECCION
        
        if len(contenido) > limite:
            logger.warning(
                "Contenido de '%s...' excede %d caracteres; se trunca como salvaguarda.",
                titulo_actual[:60], limite
            )
            contenido = contenido[:limite].rstrip() + "…"

        return contenido

    # -------------------------------------------------------------------------
    # MÉTODOS PÚBLICOS DE RESOLUCIÓN
    # -------------------------------------------------------------------------

    def resolver_contenido_seccion(self, seccion_id: str) -> dict | None:
        """
        Recupera el contenido real de una sección intentando primero parsear el 
        Markdown original (título actual -> título siguiente) para mayor fidelidad.
        Si falla, actúa como fallback haciendo un lookup directo desde el JSON cacheado.
        Mantiene trazabilidad completa combinando metadata del grafo + texto fuente.
        """
        sec_meta = self.secciones.get(seccion_id)
        if not sec_meta:
            logger.warning("seccion_id no encontrado en el grafo: %s", seccion_id)
            return None

        doc_original_id = str(sec_meta.get("documento_id", ""))
        fuente = self.fuente_documentos.get(doc_original_id)
        if not fuente:
            logger.warning("No hay documento fuente cargado para documento_id: %s", doc_original_id)
            return None

        try:
            idx = int(seccion_id.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            logger.warning("No se pudo derivar el índice de sección desde: %s", seccion_id)
            return None

        secciones_raw = fuente["secciones"]
        if idx >= len(secciones_raw):
            logger.warning("Índice %d fuera de rango para documento %s", idx, doc_original_id)
            return None

        dominio = fuente["dominio"]
        documento_nombre = sec_meta.get("documento_nombre", "")
        titulo_actual = str(secciones_raw[idx].get("titulo", sec_meta.get("titulo", ""))).strip()

        # 1. Intento principal: Extraer text enriquecido directo de Markdown
        texto = self._extraer_contenido_desde_markdown(
            documento_nombre=documento_nombre,
            dominio=dominio,
            titulo_actual=titulo_actual,
            secciones_raw=secciones_raw,
            idx=idx,
        )

        # 2. Fallback: Lookup directo ultra-rápido en caso de que no se pueda leer el .md
        if not texto:
            sec_raw = secciones_raw[idx]
            texto = (
                sec_raw.get("contenido")
                or sec_raw.get("texto")
                or sec_raw.get("texto_seccion")
                or titulo_actual
            )
            logger.info(
                "Fallback aplicado para seccion_id=%s: extrayendo desde JSON cacheado.", seccion_id
            )

        return {
            "texto": str(texto).strip(),
            "dominio": dominio,
        }

    def resolver_dominio_documento(self, documento_id: str) -> str | None:
        """
        Devuelve el dominio (Leyes/ISOs) de un documento sin resolver su contenido.
        Se usa para balancear la selección de secciones por dominio antes de
        pagar el costo de resolver texto completo.
        """
        fuente = self.fuente_documentos.get(str(documento_id))
        return fuente["dominio"] if fuente else None