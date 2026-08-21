from pathlib import Path

import pytest
from src.settings import ROOT_ENV_FILE, Settings


def test_settings_resuelve_rutas_del_proyecto(monkeypatch):
    """La configuración debe resolver datos y prompts desde datascience."""
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repo_root)
    monkeypatch.delenv("ROOT_DIR", raising=False)

    settings = Settings()

    assert settings.DB_DIR == repo_root / "db"
    assert settings.JSON_INPUT_DIR == repo_root / "db" / "input_json"
    assert settings.PROMPTS_DIR == repo_root / "proyecto" / "prompts"


def test_settings_usa_env_de_la_raiz():
    assert ROOT_ENV_FILE == Path(__file__).resolve().parents[3] / ".env"


def test_settings_carga_env_file_temporal(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("CONCEPTOS_TOP_POR_SECCION=11\n", encoding="utf-8")

    settings = Settings(_env_file=env_file)

    assert settings.CONCEPTOS_TOP_POR_SECCION == 11


def test_validate_graph_rag_key_requiere_deepseek():
    settings = Settings(
        _env_file=None,
        DEEPSEEK_API_KEY="",
        GEMINI_API_KEY="configured",
    )

    with pytest.raises(EnvironmentError, match="DEEPSEEK_API_KEY"):
        settings.validate_graph_rag_key()
