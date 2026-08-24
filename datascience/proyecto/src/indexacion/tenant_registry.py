"""LRU registry for isolated private tenant indexes."""
from __future__ import annotations

import json
import logging
import shutil
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import UUID

from settings import Settings, settings
from storage import oci_object_storage
from .indice_grafo import IndiceGrafo

logger = logging.getLogger("TenantIndexRegistry")


@dataclass
class _Entry:
    index: IndiceGrafo | None
    release_id: str | None
    generation: int | None
    created_at: str | None


class TenantIndexRegistry:
    def __init__(self, config: Settings = settings):
        self.settings = config
        self._cache: OrderedDict[UUID, _Entry] = OrderedDict()
        self._lock = RLock()

    def get(self, user_id: UUID) -> IndiceGrafo | None:
        with self._lock:
            entry = self._cache.get(user_id)
            if entry is None:
                entry = self._load_current(user_id)
                self._cache[user_id] = entry
                self._evict()
            else:
                self._cache.move_to_end(user_id)
            return entry.index

    def swap(self, user_id: UUID, indice: IndiceGrafo | None, release_id: str | None, generation: int) -> bool:
        with self._lock:
            current = self._cache.get(user_id)
            if current is not None and current.generation is not None and generation < current.generation:
                logger.info("Ignorando swap obsoleto para %s: %s < %s", user_id, generation, current.generation)
                return False
            self._cache[user_id] = _Entry(
                indice,
                release_id,
                generation,
                datetime.now(timezone.utc).isoformat(),
            )
            self._cache.move_to_end(user_id)
            self._evict()
            return True

    def release_info(self, user_id: UUID) -> dict[str, Any] | None:
        with self._lock:
            entry = self._cache.get(user_id)
            if entry is None:
                self.get(user_id)
                entry = self._cache.get(user_id)
            if entry is None or entry.release_id is None:
                return None
            return {
                "release_id": entry.release_id,
                "generation": entry.generation,
                "created_at": entry.created_at,
            }

    def graph(self, user_id: UUID) -> dict[str, Any]:
        with self._lock:
            entry = self._cache.get(user_id)
            if entry is None:
                self.get(user_id)
                entry = self._cache.get(user_id)
            if entry is None or entry.index is None:
                return {
                    "release_id": None,
                    "generation": None,
                    "created_at": None,
                    "json_data": {
                        "grafo_conceptual": {
                            "nivel_1_categorias": [],
                            "nivel_2_subcategorias": [],
                            "nivel_3_relaciones": [],
                        }
                    },
                }
            path = entry.index.settings.FILE_GRAFO_JSON
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            return {
                "release_id": entry.release_id,
                "generation": entry.generation,
                "created_at": entry.created_at,
                "json_data": data,
            }

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    def _load_current(self, user_id: UUID) -> _Entry:
        try:
            current = self._read_current(user_id)
        except Exception as exc:
            logger.warning("No se pudo localizar release privado de %s: %s", user_id, exc)
            return _Entry(None, None, None, None)
        if not current:
            return _Entry(None, None, None, None)
        release_id = str(current.get("release_id") or "")
        generation = int(current.get("generation", 0))
        prefix = str(current.get("prefix") or "")
        created_at = current.get("created_at")
        if not release_id or not prefix:
            return _Entry(None, None, generation, created_at)
        workspace = self.settings.DB_DIR / ".tenant-indexes" / str(user_id) / release_id
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        tenant_settings = self.settings.model_copy(update={
            "ROOT_DIR": workspace,
            "DATA_SOURCE": "oci" if self.settings.DATA_SOURCE.lower() == "oci" else "local",
            "OCI_PREFIX": prefix if self.settings.DATA_SOURCE.lower() == "oci" else self.settings.OCI_PREFIX,
            "OCI_SYNC_ON_STARTUP": False,
        })
        try:
            if self.settings.DATA_SOURCE.lower() == "oci":
                oci_object_storage.sync_release(
                    self.settings,
                    str(user_id),
                    current,
                    destination_root=tenant_settings.DB_DIR,
                )
            else:
                local_release = Path(prefix)
                if not local_release.is_absolute():
                    local_release = self.settings.DB_DIR / local_release
                source_db = local_release / "db" if (local_release / "db").exists() else local_release
                if source_db.exists():
                    shutil.copytree(source_db, tenant_settings.DB_DIR, dirs_exist_ok=True)
            return _Entry(IndiceGrafo(tenant_settings), release_id, generation, created_at)
        except Exception:
            logger.exception("No se pudo cargar release privado %s de %s", release_id, user_id)
            return _Entry(None, release_id, generation, created_at)

    def _read_current(self, user_id: UUID) -> dict[str, Any] | None:
        if self.settings.DATA_SOURCE.lower() == "oci":
            return oci_object_storage.read_current_release(self.settings, str(user_id))
        path = self.settings.DB_DIR / "tenants" / str(user_id) / "current.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None

    def _evict(self) -> None:
        limit = max(1, int(self.settings.MAX_USER_INDEX_CACHE))
        while len(self._cache) > limit:
            user_id, _ = self._cache.popitem(last=False)
            logger.info("Índice privado expulsado de caché: %s", user_id)
