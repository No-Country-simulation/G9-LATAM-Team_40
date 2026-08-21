from pathlib import Path

import pytest
from src.settings import Settings


def test_settings_resuelve_rutas_del_proyecto(monkeypatch):
    """La configuración debe resolver datos y prompts desde datascience."""
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repo_root)
    monkeypatch.delenv("ROOT_DIR", raising=False)

    settings = Settings()

    assert settings.DB_DIR == repo_root / "db"
    assert settings.JSON_INPUT_DIR == repo_root / "db" / "input_json"
    assert settings.PROMPTS_DIR == repo_root / "proyecto" / "prompts"


def test_validate_graph_rag_key_requiere_deepseek():
    settings = Settings(DEEPSEEK_API_KEY="", GEMINI_API_KEY="configured")

    with pytest.raises(EnvironmentError, match="DEEPSEEK_API_KEY"):
        settings.validate_graph_rag_key()
