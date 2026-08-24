from pathlib import Path
from uuid import uuid4

import pytest

from src.api.schemas import IndexDocumentRequest, IndexJobRequest
from src.indexacion.jobs import TenantIndexJobManager, _Superseded
from src.settings import Settings


class FakeStorage:
    def __init__(self, current=None):
        self.current = current
        self.uploaded = []
        self.deleted = []

    def download_object(self, settings, object_name, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("# contenido", encoding="utf-8")

    def upload_file(self, settings, local_path, object_name):
        self.uploaded.append(object_name)

    def read_current_release(self, settings, user_id):
        return self.current

    def write_current_release(self, settings, user_id, manifest):
        self.current = manifest

    def list_release_prefixes(self, settings, user_id):
        return []

    def delete_prefix(self, settings, prefix):
        self.deleted.append(prefix)


def request(user_id, generation=1, documents=None):
    return IndexJobRequest(
        user_id=user_id,
        generation=generation,
        idempotency_key=f"{user_id}:{generation}",
        documentos=documents or [],
    )


def test_same_idempotency_key_returns_existing_job(tmp_path):
    manager = TenantIndexJobManager(Settings(ROOT_DIR=tmp_path), storage_module=FakeStorage())
    user_id = uuid4()
    first = manager.create(request(user_id))
    second = manager.create(request(user_id))
    assert second.job_id == first.job_id
    manager.close()


def test_object_path_of_other_user_is_rejected(tmp_path):
    manager = TenantIndexJobManager(Settings(ROOT_DIR=tmp_path), storage_module=FakeStorage())
    user_id = uuid4()
    document = IndexDocumentRequest(
        archivo_id=uuid4(), documento_id="doc", nombre_original="doc.md", dominio="LEYES",
        object_name=f"prod/users/{uuid4()}/input/LEYES/doc.md",
    )
    with pytest.raises(ValueError):
        manager.create(request(user_id, documents=[document]))
    manager.close()


def test_newer_current_release_supersedes_without_publish(tmp_path):
    user_id = uuid4()
    storage = FakeStorage({
        "release_id": "newer",
        "prefix": f"prod/users/{user_id}/releases/newer",
        "generation": 5,
    })
    manager = TenantIndexJobManager(Settings(ROOT_DIR=tmp_path), storage_module=storage)
    job_request = request(user_id, generation=4)
    with pytest.raises(_Superseded):
        manager._publish(job_request, uuid4(), tmp_path)
    assert storage.uploaded == []
    manager.close()
