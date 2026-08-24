from uuid import uuid4

from src.indexacion.tenant_registry import TenantIndexRegistry
from src.settings import Settings


def test_swap_rechaza_generacion_menor(tmp_path):
    settings = Settings(ROOT_DIR=tmp_path, MAX_USER_INDEX_CACHE=2)
    registry = TenantIndexRegistry(settings)
    user_id = uuid4()
    assert registry.swap(user_id, object(), "release-new", 4) is True
    assert registry.swap(user_id, object(), "release-old", 3) is False
    assert registry.release_info(user_id)["release_id"] == "release-new"


def test_cache_lru_expulsa_usuario_mas_antiguo(tmp_path):
    settings = Settings(ROOT_DIR=tmp_path, MAX_USER_INDEX_CACHE=1)
    registry = TenantIndexRegistry(settings)
    first, second = uuid4(), uuid4()
    registry.swap(first, object(), "r1", 1)
    registry.swap(second, object(), "r2", 1)
    assert registry.size == 1
    assert registry.release_info(second)["release_id"] == "r2"
    assert registry.release_info(first) is None
