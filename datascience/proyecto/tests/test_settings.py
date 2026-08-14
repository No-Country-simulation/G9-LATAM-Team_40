from pathlib import Path

from src.settings import Settings


def test_settings_carga_env_desde_proyecto_por_defecto(monkeypatch):
    """La app debe leer .env desde la carpeta proyecto aunque se ejecute desde la raíz del repo."""
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repo_root)

    settings = Settings()

    assert settings.GEMINI_API_KEY or settings.DEEPSEEK_API_KEY
