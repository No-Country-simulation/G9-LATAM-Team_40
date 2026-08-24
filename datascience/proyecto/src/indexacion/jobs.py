"""Asynchronous, atomic private GraphRAG release builder."""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import UUID, uuid4

from settings import Settings, settings
from storage import oci_object_storage
from .indice_grafo import IndiceGrafo
from .tenant_registry import TenantIndexRegistry
from api.schemas import IndexDocumentRequest, IndexJobRequest, IndexJobResponse

logger = logging.getLogger("TenantIndexJobManager")


@dataclass
class _Job:
    request: IndexJobRequest
    response: IndexJobResponse
    future: Future[Any] | None = None


class TenantIndexJobManager:
    def __init__(
        self,
        config: Settings = settings,
        registry: TenantIndexRegistry | None = None,
        storage_module: Any = oci_object_storage,
    ):
        self.settings = config
        self.registry = registry or TenantIndexRegistry(config)
        self.storage = storage_module
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tenant-index")
        self._jobs: dict[UUID, _Job] = {}
        self._by_key: dict[str, UUID] = {}
        self._lock = RLock()

    def create(self, request: IndexJobRequest) -> IndexJobResponse:
        self._validate_request(request)
        with self._lock:
            existing_id = self._by_key.get(request.idempotency_key)
            if existing_id is not None:
                return self._jobs[existing_id].response
            now = datetime.now(timezone.utc)
            job_id = uuid4()
            response = IndexJobResponse(
                job_id=job_id,
                status="QUEUED",
                stage="DOWNLOAD",
                message="Job de indexación privado en cola.",
                release_id=None,
                generation=request.generation,
                created_at=now,
            )
            job = _Job(request=request, response=response)
            self._jobs[job_id] = job
            self._by_key[request.idempotency_key] = job_id
            job.future = self.executor.submit(self._run, job_id)
            return response

    def get(self, job_id: UUID) -> IndexJobResponse | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return job.response if job else None

    def close(self) -> None:
        self.executor.shutdown(wait=True, cancel_futures=False)

    def _validate_request(self, request: IndexJobRequest) -> None:
        expected_key = f"{request.user_id}:{request.generation}"
        if request.idempotency_key != expected_key:
            raise ValueError("idempotency_key debe ser '<user_id>:<generation>'")
        base = f"{self.settings.OCI_PREFIX.strip('/')}/users/{request.user_id}/input/"
        seen_files: set[UUID] = set()
        seen_docs: set[str] = set()
        for document in request.documentos:
            if document.archivo_id in seen_files or document.documento_id in seen_docs:
                raise ValueError("La lista de documentos contiene IDs duplicados")
            seen_files.add(document.archivo_id)
            seen_docs.add(document.documento_id)
            if document.dominio not in ("ISOS", "LEYES"):
                raise ValueError("dominio debe ser ISOS o LEYES")
            expected_domain = f"{base}{document.dominio}/"
            if not document.object_name.startswith(expected_domain):
                raise ValueError("object_name no pertenece al usuario y dominio indicados")
            if ".." in document.object_name or "\\" in document.object_name or "//" in document.object_name:
                raise ValueError("object_name contiene una ruta insegura")
            extension = Path(document.object_name).suffix.lower()
            if extension not in (".pdf", ".txt", ".md"):
                raise ValueError("Solo se aceptan objetos PDF, TXT o MD")

    def _run(self, job_id: UUID) -> None:
        try:
            job = self._jobs[job_id]
            workspace = self.settings.DB_DIR / ".tenant-workspaces" / str(job.request.user_id) / str(job_id)
            self._set_status(
                job_id,
                status="RUNNING",
                stage="DOWNLOAD",
                message="Preparando workspace aislado.",
                started_at=datetime.now(timezone.utc),
            )
            if workspace.exists():
                shutil.rmtree(workspace)
            (workspace / "db").mkdir(parents=True, exist_ok=True)
            self._download_documents(job.request, workspace)
            self._write_document_manifest(job.request, workspace)
            self._copy_base_config(workspace)

            for stage in ("CLEAN", "EXTRACT", "CLASSIFY", "GRAPH"):
                self._set_status(job_id, stage=stage, message=f"Ejecutando etapa {stage}.")
            self._run_build(workspace)
            self._set_status(job_id, stage="PUBLISH", message="Publicando artefactos del release privado.")
            release = self._publish(job.request, job_id, workspace)
            self._set_status(job_id, stage="RELOAD", message="Activando el release en memoria.", release_id=release["release_id"])
            self._reload_registry(job.request.user_id, job.request, workspace, release)
            if job.request.purge_previous_releases:
                self._set_status(job_id, stage="PURGE", message="Purgando releases privados anteriores.", release_id=release["release_id"])
                self._purge_previous(job.request.user_id, release["prefix"], job_id)
            self._set_status(
                job_id,
                status="SUCCEEDED",
                stage="PURGE",
                message="Release privado publicado correctamente.",
                release_id=release["release_id"],
                finished_at=datetime.now(timezone.utc),
            )
        except _Superseded as exc:
            self._set_status(
                job_id,
                status="SUPERSEDED",
                stage="PUBLISH",
                message=str(exc),
                finished_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            logger.exception("Falló el job privado %s", job_id)
            self._set_status(
                job_id,
                status="FAILED",
                stage=self._jobs[job_id].response.stage or "DOWNLOAD",
                message=str(exc),
                finished_at=datetime.now(timezone.utc),
            )

    def _download_documents(self, request: IndexJobRequest, workspace: Path) -> None:
        for document in request.documentos:
            extension = Path(document.object_name).suffix.lower()
            destination = workspace / "db" / "archivos" / document.dominio / "pdf" / f"{document.documento_id}{extension}"
            destination.parent.mkdir(parents=True, exist_ok=True)
            self.storage.download_object(self.settings, document.object_name, destination)

    def _write_document_manifest(self, request: IndexJobRequest, workspace: Path) -> None:
        manifest = {
            "document_count": len(request.documentos),
            "documents": [document.model_dump(mode="json") for document in request.documentos],
        }
        path = workspace / "db" / "input_json" / "document_manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def _copy_base_config(self, workspace: Path) -> None:
        destination = workspace / "db" / "input_json"
        destination.mkdir(parents=True, exist_ok=True)
        required = (
            "cleaning_rules.json",
            "rules.json",
            "relations.json",
            "glosario.json",
            "taxonomia_descubierta.json",
        )
        for filename in required:
            source = (
                self.settings.FILE_TAXONOMIA_DESCUBIERTA
                if filename == "taxonomia_descubierta.json"
                else self.settings.JSON_INPUT_DIR / filename
            )
            if not source.exists():
                raise RuntimeError(f"BASE_CONFIG_MISSING: {filename}")
            shutil.copy2(source, destination / filename)
            if filename == "taxonomia_descubierta.json":
                output_path = workspace / "db" / "output_json" / filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, output_path)

    def _run_build(self, workspace: Path) -> None:
        env = dict(__import__("os").environ)
        env["ROOT_DIR"] = str(workspace)
        script = self.settings.ROOT_DIR / "scripts" / "run_pipeline.py"
        completed = subprocess.run(
            [sys.executable, str(script), "--etapa", "build"],
            cwd=str(self.settings.ROOT_DIR),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"El pipeline privado falló: {completed.stderr[-2000:]}")

    def _publish(self, request: IndexJobRequest, job_id: UUID, workspace: Path) -> dict[str, Any]:
        current = self.storage.read_current_release(self.settings, str(request.user_id))
        if current and int(current.get("generation", -1)) > request.generation:
            raise _Superseded("Una generación posterior ya está publicada.")
        if current and int(current.get("generation", -1)) == request.generation:
            return {
                "release_id": str(current.get("release_id")),
                "prefix": str(current.get("prefix")),
                "generation": request.generation,
                "created_at": current.get("created_at"),
            }

        release_id = str(job_id)
        prefix = f"{self.settings.OCI_PREFIX.strip('/')}/users/{request.user_id}/releases/{release_id}"
        db_dir = workspace / "db"
        files = [
            path for root in (db_dir / "archivos", db_dir / "output_json")
            if root.exists()
            for path in root.rglob("*")
            if path.is_file()
        ]
        manifest = db_dir / "input_json" / "document_manifest.json"
        if manifest.exists():
            files.append(manifest)
        for path in sorted(files, key=lambda item: ("embeddings_llm.json" in item.name or "grafo_nodos" in item.name, item.as_posix())):
            relative = path.relative_to(db_dir).as_posix()
            self.storage.upload_file(self.settings, path, f"{prefix}/{relative}")

        latest = self.storage.read_current_release(self.settings, str(request.user_id))
        if latest and int(latest.get("generation", -1)) >= request.generation:
            if int(latest.get("generation", -1)) > request.generation:
                raise _Superseded("Una generación posterior se publicó durante la carga.")
            return latest

        current_manifest = {
            "release_id": release_id,
            "prefix": prefix,
            "generation": request.generation,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "document_count": len(request.documentos),
        }
        self.storage.write_current_release(self.settings, str(request.user_id), current_manifest)
        return current_manifest

    def _reload_registry(self, user_id: UUID, request: IndexJobRequest, workspace: Path, release: dict[str, Any]) -> None:
        if not request.documentos:
            self.registry.swap(user_id, None, release["release_id"], request.generation)
            return
        tenant_settings = self.settings.model_copy(update={
            "ROOT_DIR": workspace,
            "DATA_SOURCE": "local",
            "OCI_SYNC_ON_STARTUP": False,
        })
        indice = IndiceGrafo(tenant_settings)
        self.registry.swap(user_id, indice, release["release_id"], request.generation)

    def _purge_previous(self, user_id: UUID, active_prefix: str, job_id: UUID) -> None:
        for prefix in self.storage.list_release_prefixes(self.settings, str(user_id)):
            if prefix.rstrip("/") != active_prefix.rstrip("/"):
                self.storage.delete_prefix(self.settings, prefix)
        tenant_root = self.settings.DB_DIR / ".tenant-workspaces" / str(user_id)
        if tenant_root.exists():
            for path in tenant_root.iterdir():
                if path.name != str(job_id) and path.is_dir():
                    shutil.rmtree(path)

    def _set_status(self, job_id: UUID, **changes: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            data = job.response.model_dump()
            data.update(changes)
            job.response = IndexJobResponse(**data)


class _Superseded(RuntimeError):
    pass
