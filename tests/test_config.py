"""Testes das configurações carregadas pelo ambiente."""

from __future__ import annotations

import pytest

from src.config import Settings

ENVIRONMENT_VARIABLES = (
    "OLLAMA_HOST",
    "OLLAMA_MODEL",
    "OLLAMA_TEMPERATURE",
    "OLLAMA_TIMEOUT_SECONDS",
    "LOG_LEVEL",
)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isola os testes dos valores carregados de um .env local real."""
    for variable_name in ENVIRONMENT_VARIABLES:
        monkeypatch.delenv(variable_name, raising=False)


def test_uses_default_settings_when_environment_is_missing() -> None:
    settings = Settings()

    assert settings.ollama_host == "http://localhost:11434"
    assert settings.ollama_model == "qwen3:8b"
    assert settings.ollama_temperature == 0.2
    assert settings.ollama_timeout_seconds == 120.0
    assert settings.log_level == "INFO"


def test_environment_variables_override_default_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.example:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "modelo-teste")
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "0.35")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = Settings()

    assert settings.ollama_host == "http://ollama.example:11434"
    assert settings.ollama_model == "modelo-teste"
    assert settings.ollama_temperature == 0.35
    assert settings.ollama_timeout_seconds == 45.0
    assert settings.log_level == "DEBUG"


def test_empty_environment_values_use_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_MODEL", "   ")
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "")

    settings = Settings()

    assert settings.ollama_model == "qwen3:8b"
    assert settings.ollama_temperature == 0.2


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
        Settings()
