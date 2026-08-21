"""
Módulo para cargar el Grafo JSON, el Store de Embeddings y resolver el contenido
fuente de las secciones bajo demanda (por documento_id + título, sin re-embeber
por consulta). También carga (liviano, completo, una sola vez) la clasificación
de cada documento -- categoría + palabras clave -- generada en la Etapa 2.

ESQUEMA REAL DEL GRAFO (el que efectivamente guarda graph_builder.py):
    grafo_conceptual
      ├── nivel_1_categorias    (CAT / N1)  id, titulo, confianza
      ├── nivel_2_subcategorias (SEC / N2)  id, parent_id -> CAT, titulo_nodo_2,
      │                                     secciones: [{documento_id, titulo}, ...]
      └── nivel_3_relaciones    (REL / N3)  id, parent_id -> SEC, titulonodo_nivel_3,
                                             relaciones: [{documento_id, titulo_seccion, ...}, ...]

FLUJO DE RESOLUCIÓN (alineado al flujo usuario -> embedding -> búsqueda vectorial
-> filtrado -> recorrer grafo REL->SEC->CAT -> construir contexto -> RAG):
    1. Los embeddings en FILE_EMBEDDINGS_JSON están indexados por el id de CUALQUIER
       nivel (CAT, SEC o REL), ya que graph_builder los genera para los tres niveles.
    2. Dado un nodo top-K (de cualquier nivel), se sube por parent_id hasta ubicar
       el/los nodo(s) SEC (nivel_2) asociados.
    3. Cada nodo SEC trae una lista de referencias {documento_id, titulo}. Cada una
       de esas referencias se resuelve SOLO EN ESE MOMENTO (bajo demanda) yendo al
       archivo fuente real del documento: '<documento_id>.secciones.json', ubicado
       en la misma carpeta que su .md (settings.RUTAS_CATEGORIAS -> output_dir).
       Si el archivo no existe localmente y DATA_SOURCE=oci, se descarga puntualmente
       desde Object Storage (ver storage/oci_object_storage.fetch_document_on_demand)
       y luego se cachea en memoria para el resto de la sesión del proceso.

CONTENIDO FUENTE POR DOCUMENTO:
    Cada documento vive en su propio archivo, ej:
        db/archivos/LEYES/md/Decreto-1_02-MAY-2013.secciones.json
    El documento_id es el nombre de archivo SIN el sufijo '.secciones.json'
    (= 'Decreto-1_02-MAY-2013'), que es el mismo id que usa el grafo y el mismo
    nombre que su .md correspondiente (para el fallback de re-parseo de Markdown).

CLASIFICACIÓN POR DOCUMENTO (categoría + palabras clave):
    Se lee de settings.FILE_ISO_CLASIFICADO y settings.FILE_LEYES_CLASIFICADO,
    con este esquema real (salida de la Etapa 2 - clasificación LLM):
        {
          "documento_id": "...",
          "clasificaciones": [
            {"cluster_id": "...", "categoria": "...", "confianza": 0.95,
             "palabras_claves": ["...", "..."]}
          ]
        }
    Un documento puede tener varias clasificaciones (varios clusters). Se toma
    la de mayor "confianza" como representativa a nivel documento (esto es a
    propósito más simple que resolver por sección: la categoría/keywords que
    se exponen en trazabilidad son "la categoría principal del documento", no
    una por cada sección individual).
    Estos dos archivos son livianos (metadata, no contenido completo de
    secciones), así que se cargan COMPLETOS una sola vez al iniciar, igual que
    el grafo y los embeddings -- no son lazy como los .secciones.json.

NOTA IMPORTANTE (cambio respecto a la versión anterior):
    Ya NO se precargan todos los .secciones.json de todos los documentos al
    iniciar. Solo se resuelven (y descargan de OCI si hace falta) los documentos
    que efectivamente aparecen en la trazabilidad de una consulta, la primera
    vez que se necesitan. Esto evita bajar/parsear el corpus completo si una
    consulta puntual solo necesita 2-3 documentos.
"""
from __future__ import annotations

import difflib
import json
import logging
import re
from pathlib import Path

from settings import settings
from storage.oci_object_storage import fetch_document_on_demand, ObjectNotFoundError

logger = logging.getLogger("IndiceGrafo")

# Umbral mínimo de similitud (0-1) para aceptar un match aproximado de título
# cuando el match exacto y el normalizado fallan. Por debajo de esto, se
# descarta el candidato en vez de arriesgar un contenido incorrecto.
UMBRAL_SIMILITUD_TITULO_FUZZY = 0.72

_PATRON_RUIDO_MARKDOWN = re.compile(r"[*#_`>]+")
_PATRON_ESPACIOS = re.compile(r"\s+")


def _normalizar_titulo(texto: str) -> str:
    """
    Normaliza un título para comparación tolerante: quita símbolos de
    Markdown (**, ######, _, `, >), colapsa espacios y pasa a minúsculas.
    Esto compensa discrepancias entre el título guardado en el grafo
    (nivel_2_subcategorias[...]['secciones']) y el título real dentro del
    '<documento_id>.secciones.json' fuente, cuando alguna etapa previa
    (extracción/clasificación/construcción del grafo) dejó el título con
    formato crudo, recortado o con encabezados concatenados.
    """
    if not texto:
        return ""
    limpio = _PATRON_RUIDO_MARKDOWN.sub(" ", texto)
    limpio = _PATRON_ESPACIOS.sub(" ", limpio)
    return limpio.strip().lower()


class IndiceGrafo:
    """Carga el Grafo JSON, los Embeddings y las clasificaciones en memoria;
    resuelve el contenido fuente de cada documento de forma perezosa (lazy),
    bajo demanda."""

    # Mapea el nombre de "dominio" tal como se quiere exponer (para trazabilidad)
    # hacia el nombre de "categoria" usado en settings.RUTAS_CATEGORIAS.
    DOMINIO_A_CARPETA = {
        "Leyes": "LEYES",
        "ISOs": "ISOS",
    }

    # Sufijo real de los archivos de contenido por sección, ej:
    # "Decreto-1_02-MAY-2013.secciones.json" -> documento_id = "Decreto-1_02-MAY-2013"
    SUFIJO_ARCHIVO_SECCIONES = ".secciones.json"

    def __init__(self):
        # --- Grafo (esquema real: 3 niveles con parent_id) ---
        self.nivel_1_categorias: dict[str, dict] = {}
        self.nivel_2_subcategorias: dict[str, dict] = {}
        self.nivel_3_relaciones: dict[str, dict] = {}

        self._cargar_grafo()
        self.embeddings_store = self._cargar_embeddings()

        # documento_id -> {"dominio", "secciones", "titulo", "source_path"} | None
        # Se llena bajo demanda en _resolver_documento_lazy. None = ya se intentó
        # resolver y no se encontró en ningún dominio (evita reintentos repetidos).
        self._cache_documentos: dict[str, dict | None] = {}
        self._cache_markdown: dict[Path, str] = {}

        # documento_id -> {"categoria": str, "palabras_clave": list[str]}
        # Metadata liviana, cargada COMPLETA una sola vez (no lazy).
        self._clasificaciones_por_documento: dict[str, dict] = self._cargar_clasificaciones()

        logger.info(
            "IndiceGrafo inicializado: %d categorías (N1), %d secciones (N2), %d relaciones (N3), "
            "%d embeddings, %d documentos clasificados. Documentos fuente se resuelven bajo demanda (lazy).",
            len(self.nivel_1_categorias), len(self.nivel_2_subcategorias), len(self.nivel_3_relaciones),
            len(self.embeddings_store), len(self._clasificaciones_por_documento)
        )

    # -------------------------------------------------------------------------
    # MÉTODOS DE CARGA E INICIALIZACIÓN
    # -------------------------------------------------------------------------

    def _cargar_grafo(self) -> None:
        """Carga los 3 niveles del grafo desde el archivo principal (esquema 'grafo_conceptual')."""
        if not settings.FILE_GRAFO_JSON.exists():
            logger.warning("El archivo de grafo no existe en: %s", settings.FILE_GRAFO_JSON)
            return

        try:
            data = json.loads(settings.FILE_GRAFO_JSON.read_text(encoding="utf-8"))
            grafo = data.get("grafo_conceptual", {})
            self.nivel_1_categorias = {n["id"]: n for n in grafo.get("nivel_1_categorias", [])}
            self.nivel_2_subcategorias = {n["id"]: n for n in grafo.get("nivel_2_subcategorias", [])}
            self.nivel_3_relaciones = {n["id"]: n for n in grafo.get("nivel_3_relaciones", [])}
            logger.info(
                "Grafo cargado exitosamente. N1=%d, N2=%d, N3=%d.",
                len(self.nivel_1_categorias), len(self.nivel_2_subcategorias), len(self.nivel_3_relaciones)
            )
        except Exception as e:
            logger.error("Error al cargar el grafo JSON: %s", e)

    def _cargar_embeddings(self) -> dict:
        """Carga el almacén de vectores JSON en memoria (ids de cualquiera de los 3 niveles)."""
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

    def _cargar_clasificaciones(self) -> dict[str, dict]:
        """
        Carga documentos_iso_clasificado_llm.json y documentos_leyes_clasificado_llm.json
        (settings.FILE_ISO_CLASIFICADO / FILE_LEYES_CLASIFICADO) y arma un índice
        documento_id -> {"categoria", "palabras_clave"}, usando la clasificación
        de mayor "confianza" cuando un documento tiene varias.
        """
        resultado: dict[str, dict] = {}

        for ruta in (settings.FILE_ISO_CLASIFICADO, settings.FILE_LEYES_CLASIFICADO):
            if not ruta.exists():
                logger.warning("Archivo de clasificación no encontrado (se omite): %s", ruta)
                continue

            try:
                data = json.loads(ruta.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("Error al leer clasificación %s: %s", ruta, e)
                continue

            documentos = data if isinstance(data, list) else [data]

            for doc in documentos:
                documento_id = doc.get("documento_id")
                clasificaciones = doc.get("clasificaciones") or []
                if not documento_id or not clasificaciones:
                    continue

                mejor = max(clasificaciones, key=lambda c: c.get("confianza", 0.0))
                resultado[documento_id] = {
                    "categoria": str(mejor.get("categoria") or "").strip(),
                    "palabras_clave": list(mejor.get("palabras_claves") or []),
                }

        logger.info("Clasificaciones cargadas para %d documentos.", len(resultado))
        return resultado

    @classmethod
    def _carpeta_a_dominio(cls, categoria_carpeta: str) -> str:
        """Inverso de DOMINIO_A_CARPETA: 'LEYES' -> 'Leyes', 'ISOS' -> 'ISOs'."""
        for dominio, carpeta in cls.DOMINIO_A_CARPETA.items():
            if carpeta == categoria_carpeta:
                return dominio
        return categoria_carpeta

    # -------------------------------------------------------------------------
    # RESOLUCIÓN PEREZOSA (LAZY) DE DOCUMENTOS FUENTE
    # -------------------------------------------------------------------------

    def _resolver_documento_lazy(self, documento_id: str) -> dict | None:
        """
        Mapeo + fetch bajo demanda: busca en qué carpeta de dominio vive
        '<documento_id>.secciones.json'. Si no está local y DATA_SOURCE=oci,
        lo descarga SOLO a él (no el bucket completo). Cachea el resultado
        (incluso los fallos) para no repetir el intento dentro del mismo proceso.
        """
        if documento_id in self._cache_documentos:
            return self._cache_documentos[documento_id]

        for ruta_cat in settings.RUTAS_CATEGORIAS:
            categoria_carpeta = ruta_cat["categoria"]          # "ISOS" | "LEYES"
            carpeta_contenido = ruta_cat["output_dir"]          # .../{categoria}/md
            dominio = self._carpeta_a_dominio(categoria_carpeta)
            local_path = carpeta_contenido / f"{documento_id}{self.SUFIJO_ARCHIVO_SECCIONES}"

            if not local_path.exists() and settings.DATA_SOURCE.lower() == "oci":
                try:
                    fetch_document_on_demand(settings, local_path)
                except ObjectNotFoundError:
                    continue  # no está en este dominio, prueba el siguiente
                except Exception as e:
                    logger.error(
                        "Error descargando de OCI '%s' para documento_id=%s: %s",
                        local_path.name, documento_id, e
                    )
                    continue

            if not local_path.exists():
                continue

            try:
                doc = json.loads(local_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("Error leyendo documento resuelto bajo demanda %s: %s", local_path, e)
                continue

            resultado = {
                "dominio": dominio,
                "secciones": doc.get("secciones", []),
                "titulo": str(doc.get("titulo") or "").strip(),
                "source_path": doc.get("source_path", ""),
            }
            self._cache_documentos[documento_id] = resultado
            logger.info("Documento resuelto y cacheado: documento_id=%s (dominio=%s)", documento_id, dominio)
            return resultado

        logger.warning("documento_id no resoluble en ningún dominio: %s", documento_id)
        self._cache_documentos[documento_id] = None
        return None

    # -------------------------------------------------------------------------
    # HELPERS DE EXTRACCIÓN MARKDOWN (fallback, por si un documento no trae texto)
    # -------------------------------------------------------------------------

    def _ruta_markdown(self, documento_id: str, dominio: str) -> Path | None:
        """Localiza el archivo .md original a partir del dominio y el documento_id."""
        carpeta = self.DOMINIO_A_CARPETA.get(dominio)
        if not carpeta:
            logger.warning("Dominio desconocido para resolución de Markdown: %s", dominio)
            return None

        nombre = f"{documento_id}.md"
        ruta = settings.ARCHIVOS_DIR / carpeta / "md" / nombre
        if ruta.exists():
            return ruta

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

    def _extraer_contenido_desde_markdown(self, documento_id: str, dominio: str, titulo_seccion: str) -> str:
        """FALLBACK: extrae el contenido desde el Markdown original si el JSON no trae texto."""
        if not titulo_seccion:
            return ""

        ruta_md = self._ruta_markdown(documento_id, dominio)
        if not ruta_md:
            return ""

        texto_md = self._leer_markdown(ruta_md)
        if not texto_md:
            return ""

        pos_inicio = texto_md.find(titulo_seccion)
        if pos_inicio == -1:
            logger.warning("Título no encontrado en el Markdown: '%s...'", titulo_seccion[:60])
            return ""

        # Corta hasta el siguiente salto de doble línea como aproximación razonable
        # (no tenemos la lista ordenada de títulos siguientes en este punto).
        pos_fin = texto_md.find("\n\n", pos_inicio + len(titulo_seccion))
        if pos_fin == -1:
            pos_fin = len(texto_md)

        return texto_md[pos_inicio:pos_fin].strip()

    # -------------------------------------------------------------------------
    # MÉTODOS PÚBLICOS DE RESOLUCIÓN (alineados al flujo REL -> SEC -> CAT)
    # -------------------------------------------------------------------------

    def resolver_nodos_seccion_desde_nodo(self, nodo_id: str) -> list[dict]:
        """
        Dado un nodo top-K de CUALQUIER nivel (id encontrado en la búsqueda vectorial
        contra embeddings_store), retorna la lista de nodos SEC (nivel_2) asociados:
          - Si nodo_id es una relación (N3): sube por parent_id hasta su SEC padre.
          - Si nodo_id ya es un SEC (N2): se retorna a sí mismo.
          - Si nodo_id es una categoría (N1): retorna todos sus SEC hijos directos.
        """
        if nodo_id in self.nivel_3_relaciones:
            parent_id = self.nivel_3_relaciones[nodo_id].get("parent_id")
            nodo_sec = self.nivel_2_subcategorias.get(parent_id)
            if not nodo_sec:
                logger.warning(
                    "Relación '%s' apunta a parent_id '%s' inexistente en nivel_2_subcategorias.",
                    nodo_id, parent_id
                )
                return []
            return [nodo_sec]

        if nodo_id in self.nivel_2_subcategorias:
            return [self.nivel_2_subcategorias[nodo_id]]

        if nodo_id in self.nivel_1_categorias:
            hijos = [
                nodo for nodo in self.nivel_2_subcategorias.values()
                if nodo.get("parent_id") == nodo_id
            ]
            if not hijos:
                logger.warning("Categoría '%s' no tiene nodos SEC hijos.", nodo_id)
            return hijos

        logger.warning("nodo_id no encontrado en ningún nivel del grafo: %s", nodo_id)
        return []

    def resolver_contenido_nodo_seccion(self, nodo_sec: dict) -> list[dict]:
        """
        Dado un nodo SEC (nivel_2_subcategorias), resuelve el contenido real
        (texto + trazabilidad) de cada referencia {documento_id, titulo} que agrupa,
        yendo al archivo fuente '<documento_id>.secciones.json' correspondiente
        (bajo demanda, vía _resolver_documento_lazy).
        """
        resultados: list[dict] = []
        for ref in nodo_sec.get("secciones", []):
            documento_id = str(ref.get("documento_id", "")).strip()
            titulo_seccion = str(ref.get("titulo", "")).strip()

            resuelto = self.resolver_contenido_por_documento_y_titulo(documento_id, titulo_seccion)
            if resuelto:
                resultados.append({
                    "documento_id": documento_id,
                    "titulo_seccion": titulo_seccion,
                    **resuelto,
                })
        return resultados

    def resolver_contenido_por_documento_y_titulo(self, documento_id: str, titulo_seccion: str) -> dict | None:
        """
        Localiza, dentro del archivo fuente de 'documento_id' (resuelto bajo demanda,
        descargándolo de OCI si hace falta), la sección cuyo título coincide
        exactamente con 'titulo_seccion', y devuelve su texto + trazabilidad
        (dominio, nivel, ruta_jerarquica, source_path).

        LIMITACIÓN CONOCIDA: como el grafo solo guarda {documento_id, titulo} (sin
        índice ni línea), si el mismo documento tiene dos secciones con títulos
        idénticos (o ambas con título vacío), se toma la primera coincidencia y se
        registra un warning. Para eliminar esta ambigüedad, habría que agregar en
        graph_builder.py un dato adicional (ej. 'linea_inicio' o el índice de la
        sección) a cada referencia en nivel_2_subcategorias['secciones'].
        """
        fuente = self._resolver_documento_lazy(documento_id)
        if not fuente:
            logger.warning(
                "No hay documento fuente resoluble para documento_id: %s "
                "(verifica que exista '%s%s' local o en OCI bajo el prefijo correcto)",
                documento_id, documento_id, self.SUFIJO_ARCHIVO_SECCIONES
            )
            return None

        secciones_raw = fuente["secciones"]
        titulo_norm = titulo_seccion.strip()

        # 1) Match exacto (comportamiento original, el más confiable).
        candidatos = [s for s in secciones_raw if str(s.get("titulo", "")).strip() == titulo_norm]

        # 2) Match normalizado (ignora **, ######, espacios extra, mayúsculas).
        #    Cubre el caso típico de un título guardado con formato Markdown
        #    crudo en el grafo pero limpio en el archivo fuente, o viceversa.
        sec_raw = None
        if candidatos:
            if len(candidatos) > 1:
                logger.warning(
                    "Título de sección ambiguo ('%s') con %d coincidencias exactas en '%s'; se usa la primera.",
                    titulo_norm[:60] or "(vacío)", len(candidatos), documento_id
                )
            sec_raw = candidatos[0]
        else:
            titulo_norm_limpio = _normalizar_titulo(titulo_norm)
            candidatos_normalizados = [
                s for s in secciones_raw
                if _normalizar_titulo(str(s.get("titulo", ""))) == titulo_norm_limpio
            ] if titulo_norm_limpio else []

            if candidatos_normalizados:
                if len(candidatos_normalizados) > 1:
                    logger.warning(
                        "Título de sección ambiguo tras normalizar ('%s') con %d coincidencias en '%s'; "
                        "se usa la primera.",
                        titulo_norm[:60] or "(vacío)", len(candidatos_normalizados), documento_id
                    )
                sec_raw = candidatos_normalizados[0]
                logger.info(
                    "Sección resuelta por match NORMALIZADO (no exacto) para documento_id=%s: '%s'",
                    documento_id, titulo_norm[:60]
                )
            else:
                # 3) Último recurso: coincidencia difusa (difflib) sobre los
                #    títulos normalizados disponibles en el documento.
                titulos_disponibles = {
                    _normalizar_titulo(str(s.get("titulo", ""))): s for s in secciones_raw
                }
                mejores = difflib.get_close_matches(
                    titulo_norm_limpio, titulos_disponibles.keys(),
                    n=1, cutoff=UMBRAL_SIMILITUD_TITULO_FUZZY
                )
                if mejores:
                    sec_raw = titulos_disponibles[mejores[0]]
                    logger.warning(
                        "Sección resuelta por match APROXIMADO (fuzzy) para documento_id=%s: "
                        "buscado='%s' | usado='%s'",
                        documento_id, titulo_norm[:60], mejores[0][:60]
                    )

        if sec_raw is None:
            logger.warning(
                "No se encontró sección con título '%s' dentro del documento '%s' "
                "(ni exacto, ni normalizado, ni aproximado por encima de %.2f).",
                titulo_norm[:60] or "(vacío)", documento_id, UMBRAL_SIMILITUD_TITULO_FUZZY
            )
            return None

        # 1. Fuente primaria: texto ya extraído/limpiado en Etapa 1.
        texto = sec_raw.get("texto") or sec_raw.get("contenido") or sec_raw.get("texto_seccion")

        # 2. Fallback: reparseo del Markdown original si el JSON no trae texto.
        if not texto:
            texto = self._extraer_contenido_desde_markdown(
                documento_id=documento_id,
                dominio=fuente["dominio"],
                titulo_seccion=titulo_norm,
            )

        # 3. Último recurso: usar el título.
        if not texto:
            texto = titulo_norm
            logger.warning(
                "Sin contenido resoluble para documento_id=%s, titulo='%s'; se usa solo el título.",
                documento_id, titulo_norm[:60]
            )

        texto = str(texto).strip()
        limite = settings.MAX_CARACTERES_CONTENIDO_SECCION
        if len(texto) > limite:
            texto = texto[:limite].rstrip() + "…"

        return {
            "texto": texto,
            "dominio": fuente["dominio"],
            "nivel": sec_raw.get("nivel"),
            "ruta_jerarquica": sec_raw.get("ruta_jerarquica", []),
            "source_path": fuente.get("source_path", ""),
        }

    def resolver_dominio_documento(self, documento_id: str) -> str | None:
        """Devuelve el dominio (Leyes/ISOs) de un documento sin resolver su contenido."""
        fuente = self._resolver_documento_lazy(str(documento_id))
        return fuente["dominio"] if fuente else None

    def obtener_info_documento(self, documento_id: str) -> dict:
        """
        Reemplazo lazy de lo que antes era 'self.indice.fuente_documentos.get(documento_id, {})'.
        Resuelve (y cachea/descarga de OCI si hace falta) el documento y devuelve su
        metadata básica: {"dominio", "titulo", "source_path"}. Devuelve {} si no existe,
        igual que el .get(documento_id, {}) original.
        """
        fuente = self._resolver_documento_lazy(str(documento_id))
        if not fuente:
            return {}
        return {
            "dominio": fuente["dominio"],
            "titulo": fuente["titulo"],
            "source_path": fuente.get("source_path", ""),
        }

    def obtener_categoria_y_palabras_clave(self, documento_id: str) -> dict:
        """
        Devuelve la categoría principal y las palabras clave del documento,
        según la clasificación de mayor confianza (Etapa 2). No dispara ninguna
        descarga (los archivos de clasificación ya están completos en memoria
        desde __init__). Devuelve {"categoria": "", "palabras_clave": []} si el
        documento no tiene clasificación registrada.
        """
        return self._clasificaciones_por_documento.get(
            str(documento_id), {"categoria": "", "palabras_clave": []}
        )