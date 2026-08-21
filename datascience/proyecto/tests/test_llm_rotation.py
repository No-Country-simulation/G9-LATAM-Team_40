"""Pruebas unitarias para la rotación y fallback de clientes LLM."""
import pytest
from settings import settings


def test_gemini_models_fallback_list():
    """Verifica que la lista de modelos de fallback de Gemini contenga los modelos esperados."""
    modelos = settings.GEMINI_MODELS
    assert len(modelos) >= 2
    assert "gemini-3.5-flash-lite" in modelos
    assert "gemini-3.1-flash-lite" in modelos


def test_deepseek_configuration():
    """Verifica que la configuración base de DeepSeek esté correctamente definida."""
    assert settings.DEEPSEEK_MODEL == "deepseek-chat"
    assert "deepseek" in settings.DEEPSEEK_BASE_URL