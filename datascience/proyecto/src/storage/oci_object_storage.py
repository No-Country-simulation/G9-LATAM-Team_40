"""Synchronize the local GraphRAG data directory from OCI Object Storage.

Dos modos de uso:

1. sync_db_from_oci(settings)
   Descarga TODO lo que esté bajo OCI_PREFIX (grafo, embeddings y TODOS los
   .secciones.json de todos los documentos). Útil para un precache manual
   completo, pero NO se usa por defecto en el arranque de la API.

2. sync_metadata_from_oci(settings)
   Descarga SOLO el grafo y los embeddings (los artefactos livianos que la
   búsqueda vectorial necesita siempre). Es lo que se ejecuta en el arranque
   de la API (app.py).

3. fetch_document_on_demand(settings, local_path)
   Descarga UN SOLO objeto (típicamente un '<documento_id>.secciones.json')
   solo si aún no existe localmente. Lo usa IndiceGrafo para resolver el
   contenido real de una sección SOLO cuando esa sección aparece en la
   trazabilidad de una consulta (no antes).

Estructura esperada en el bucket (espejo de settings.DB_DIR, bajo OCI_PREFIX):

    prod/output_json/grafo_nodos_subnodos_graphrag.json
    prod/output_json/embeddings_llm.json
    prod/archivos/ISOS/md/<documento_id>.secciones.json
    prod/archivos/LEYES/md/<documento_id>.secciones.json
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import oci

from settings import Settings

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = ".oci_sync_manifest.json"


class ObjectNotFoundError(Exception):
    """El objeto solicitado no existe en el bucket."""


# --------------------------------------------------------------------------
# Autenticación / cliente
# --------------------------------------------------------------------------

def _api_key_config(settings: Settings) -> dict[str, Any]:
    """Load an API-key configuration from OCI config or CLI environment variables."""
    config_file = settings.OCI_CONFIG_FILE or os.getenv("OCI_CLI_CONFIG_FILE")
    profile = settings.OCI_CONFIG_PROFILE

    if config_file or (Path.home() / ".oci" / "config").exists():
        return oci.config.from_file(
            file_location=config_file or "~/.oci/config",
            profile_name=profile,
        )

    config = {
        "user": os.getenv("OCI_CLI_USER", ""),
        "tenancy": os.getenv("OCI_CLI_TENANCY", ""),
        "region": os.getenv("OCI_CLI_REGION", ""),
        "fingerprint": os.getenv("OCI_CLI_FINGERPRINT", ""),
        "key_file": os.getenv("OCI_CLI_KEY_FILE", ""),
    }
    oci.config.validate_config(config)
    return config


def _object_storage_client(settings: Settings) -> oci.object_storage.ObjectStorageClient:
    mode = settings.OCI_AUTH_MODE.lower()
    if mode == "instance_principal":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        return oci.object_storage.ObjectStorageClient(config={}, signer=signer)
    if mode != "api_key":
        raise ValueError("OCI_AUTH_MODE debe ser 'api_key' o 'instance_principal'.")
    return oci.object_storage.ObjectStorageClient(_api_key_config(settings))


# --------------------------------------------------------------------------
# Manifiesto local (ETags) — usado por el sync completo
# --------------------------------------------------------------------------

def _load_manifest(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        logger.warning("No se pudo leer el manifiesto OCI local; se descargarán los objetos nuevamente.")
        return {}


def _write_manifest(path: Path, manifest: dict[str, str]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


# --------------------------------------------------------------------------
# Traducción de rutas: local <-> nombre de objeto remoto
# --------------------------------------------------------------------------

def _safe_local_path(db_dir: Path, remote_name: str, prefix: str) -> Path | None:
    """remote_name (ej. 'prod/output_json/grafo.json') -> ruta local dentro de db_dir."""
    normalized_prefix = prefix.strip("/")
    prefix_with_slash = f"{normalized_prefix}/" if normalized_prefix else ""
    if prefix_with_slash and not remote_name.startswith(prefix_with_slash):
        return None

    relative_name = remote_name[len(prefix_with_slash):] if prefix_with_slash else remote_name
    if not relative_name or relative_name.endswith("/"):
        return None

    destination = (db_dir / relative_name).resolve()
    try:
        destination.relative_to(db_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"Nombre de objeto OCI no seguro: {remote_name}") from exc
    return destination


def _object_name_for_local_path(settings: Settings, local_path: Path) -> str:
    """Traduce una ruta local dentro de DB_DIR al nombre de objeto remoto en OCI.
    Inverso de _safe_local_path. Ej:
        DB_DIR/output_json/grafo.json -> 'prod/output_json/grafo.json'
        DB_DIR/archivos/LEYES/md/X.secciones.json -> 'prod/archivos/LEYES/md/X.secciones.json'
    """
    db_dir = settings.DB_DIR.resolve()
    relative = local_path.resolve().relative_to(db_dir)
    prefix = settings.OCI_PREFIX.strip("/")
    relative_posix = relative.as_posix()
    return f"{prefix}/{relative_posix}" if prefix else relative_posix


# --------------------------------------------------------------------------
# Descarga de un objeto individual
# --------------------------------------------------------------------------

def _download_object(
    client: oci.object_storage.ObjectStorageClient,
    namespace: str,
    bucket_name: str,
    object_name: str,
    destination: Path,
) -> None:
    response = client.get_object(namespace, bucket_name, object_name)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with temporary.open("wb") as output:
            for chunk in response.data.iter_content(chunk_size=1024 * 1024):
                output.write(chunk)
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink(missing_ok=True)


def fetch_document_on_demand(
    settings: Settings,
    local_path: Path,
    client: oci.object_storage.ObjectStorageClient | None = None,
) -> Path:
    """
    Descarga UN SOLO objeto (ej. un '<documento_id>.secciones.json') desde OCI
    a 'local_path', solo si aún no existe localmente. No lista el bucket completo.
    Lanza ObjectNotFoundError si el objeto no existe en OCI (404).
    """
    if local_path.exists():
        return local_path

    if not settings.OCI_BUCKET_NAME or not settings.OCI_NAMESPACE:
        raise EnvironmentError(
            "DATA_SOURCE=oci requiere OCI_DATASET_BUCKET y OCI_NAMESPACE."
        )

    client = client or _object_storage_client(settings)
    object_name = _object_name_for_local_path(settings, local_path)

    try:
        _download_object(client, settings.OCI_NAMESPACE, settings.OCI_BUCKET_NAME, object_name, local_path)
        logger.info("Documento descargado bajo demanda: %s", object_name)
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            raise ObjectNotFoundError(object_name) from e
        raise

    return local_path


# --------------------------------------------------------------------------
# Sync liviano: SOLO grafo + embeddings (usado en el arranque de la API)
# --------------------------------------------------------------------------

def sync_metadata_from_oci(
    settings: Settings,
    client: oci.object_storage.ObjectStorageClient | None = None,
) -> None:
    """
    Sincroniza SOLO los artefactos ligeros necesarios para la búsqueda vectorial
    (grafo + embeddings), NO los .secciones.json de cada documento (esos se
    resuelven bajo demanda por consulta, vía fetch_document_on_demand).
    """
    client = client or _object_storage_client(settings)
    archivos_criticos = [settings.FILE_GRAFO_JSON, settings.FILE_EMBEDDINGS_JSON]

    for ruta_local in archivos_criticos:
        try:
            # Fuerza redescarga si ya existe una copia local vieja: para grafo/embeddings
            # sí queremos siempre la última versión al arrancar, no solo "si no existe".
            if ruta_local.exists():
                ruta_local.unlink()
            fetch_document_on_demand(settings, ruta_local, client=client)
            logger.info("Metadata sincronizada: %s", ruta_local.name)
        except ObjectNotFoundError:
            logger.warning(
                "No existe todavía en OCI: %s (¿ya corriste la Etapa 4 / graph_builder?)",
                ruta_local.name,
            )


# --------------------------------------------------------------------------
# Sync completo (legacy / precache manual): descarga TODO el prefijo
# --------------------------------------------------------------------------

def sync_db_from_oci(settings: Settings) -> dict[str, int]:
    """Download OCI_PREFIX into DB_DIR without deleting local files.
    Descarga TODO (grafo, embeddings y TODOS los .secciones.json). Útil para
    un precache manual completo, pero no se usa por defecto en el arranque."""
    if not settings.OCI_BUCKET_NAME or not settings.OCI_NAMESPACE:
        raise EnvironmentError(
            "DATA_SOURCE=oci requiere OCI_DATASET_BUCKET y OCI_NAMESPACE."
        )

    client = _object_storage_client(settings)
    db_dir = settings.DB_DIR.resolve()
    db_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = db_dir / MANIFEST_FILENAME
    manifest = _load_manifest(manifest_path)
    remote_manifest: dict[str, str] = {}
    downloaded = 0
    skipped = 0

    prefix = settings.OCI_PREFIX.strip("/")
    list_response = oci.pagination.list_call_get_all_results(
        client.list_objects,
        settings.OCI_NAMESPACE,
        settings.OCI_BUCKET_NAME,
        prefix=prefix or None,
        fields="name,size,etag",
    )

    for item in list_response.data.objects:
        destination = _safe_local_path(db_dir, item.name, prefix)
        if destination is None:
            continue

        etag = item.etag or ""
        remote_manifest[item.name] = etag
        if destination.exists() and manifest.get(item.name) == etag:
            skipped += 1
            continue

        logger.info("Descargando OCI: %s", item.name)
        _download_object(client, settings.OCI_NAMESPACE, settings.OCI_BUCKET_NAME, item.name, destination)
        downloaded += 1

    _write_manifest(manifest_path, remote_manifest)
    logger.info("Sincronización OCI completada: %d descargados, %d sin cambios.", downloaded, skipped)
    return {"downloaded": downloaded, "skipped": skipped}