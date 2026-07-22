"""Testes das configurações carregadas pelo ambiente."""

from __future__ import annotations

import importlib

import pytest

import src.config as config_module


ENVIRONMENT_VARIABLES = (
    "OLLAMA_HOST",
    "OLLAMA_MODEL",
    "OLLAMA_TEMPERATURE",
    "OLLAMA_TIMEOUT_SECONDS",
    "LOG_LEVEL",
)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove configurações externas para isolar cada teste."""
    for variable_name in ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(variable_name, raising=False)


def reload_config():
    """Recarrega o módulo para reconstruir a instância SETTINGS."""
    return importlib.reload(config_module)


def test_uses_default_settings_when_environment_is_missing() -> None:
    config = reload_config()

    assert config.SETTINGS.ollama_host == "http://localhost:11434"
    assert config.SETTINGS.ollama_model == "qwen3:8b"
    assert config.SETTINGS.ollama_temperature == 0.2
    assert config.SETTINGS.ollama_timeout_seconds == 120.0
    assert config.SETTINGS.log_level == "INFO"


def test_environment_variables_override_default_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.example:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "modelo-teste")
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "0.35")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    config = reload_config()

    assert config.SETTINGS.ollama_host == "http://ollama.example:11434"
    assert config.SETTINGS.ollama_model == "modelo-teste"
    assert config.SETTINGS.ollama_temperature == 0.35
    assert config.SETTINGS.ollama_timeout_seconds == 45.0
    assert config.SETTINGS.log_level == "DEBUG"


def test_empty_environment_values_use_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_MODEL", "   ")
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "")

    config = reload_config()

    assert config.SETTINGS.ollama_model == "qwen3:8b"
    assert config.SETTINGS.ollama_temperature == 0.2


@pytest.mark.parametrize(
    ("variable_name", "invalid_value"),
    [
        ("OLLAMA_TEMPERATURE", "baixa"),
        ("OLLAMA_TIMEOUT_SECONDS", "um minuto"),
    ],
)
def test_rejects_invalid_numeric_environment_values(
    monkeypatch: pytest.MonkeyPatch,
    variable_name: str,
    invalid_value: str,
) -> None:
    monkeypatch.setenv(variable_name, invalid_value)

    with pytest.raises(ValueError, match=variable_name):
        reload_config()
