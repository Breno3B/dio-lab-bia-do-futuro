"""Testes das configurações carregadas pelo ambiente."""

from __future__ import annotations

import pytest

from src.config import Settings


ENVIRONMENT_VARIABLES = (
    "OLLAMA_HOST",
    "OLLAMA_MODEL",
    "OLLAMA_TEMPERATURE",
    "OLLAMA_TIMEOUT_SECONDS",
    "OLLAMA_NUM_CTX",
    "OLLAMA_NUM_PREDICT",
    "MAX_USER_MESSAGE_CHARS",
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
    assert settings.ollama_model == "qwen3:4b"
    assert settings.ollama_temperature == 0.2
    assert settings.ollama_timeout_seconds == 180.0
    assert settings.ollama_num_ctx == 4096
    assert settings.ollama_num_predict == 250
    assert settings.max_user_message_chars == 2000
    assert settings.log_level == "INFO"


def test_environment_variables_override_default_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://ollama.example:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "modelo-teste")
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "0.35")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "8192")
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "400")
    monkeypatch.setenv("MAX_USER_MESSAGE_CHARS", "3500")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = Settings()

    assert settings.ollama_host == "http://ollama.example:11434"
    assert settings.ollama_model == "modelo-teste"
    assert settings.ollama_temperature == 0.35
    assert settings.ollama_timeout_seconds == 45.0
    assert settings.ollama_num_ctx == 8192
    assert settings.ollama_num_predict == 400
    assert settings.max_user_message_chars == 3500
    assert settings.log_level == "DEBUG"


def test_empty_environment_values_use_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_MODEL", " ")
    monkeypatch.setenv("OLLAMA_TEMPERATURE", "")
    monkeypatch.setenv("OLLAMA_NUM_CTX", " ")
    monkeypatch.setenv("MAX_USER_MESSAGE_CHARS", "")

    settings = Settings()

    assert settings.ollama_model == "qwen3:4b"
    assert settings.ollama_temperature == 0.2
    assert settings.ollama_num_ctx == 4096
    assert settings.max_user_message_chars == 2000


@pytest.mark.parametrize(
    ("variable_name", "invalid_value"),
    [
        ("OLLAMA_TEMPERATURE", "baixa"),
        ("OLLAMA_TIMEOUT_SECONDS", "um minuto"),
        ("OLLAMA_NUM_CTX", "quatro mil"),
        ("OLLAMA_NUM_PREDICT", "duzentos"),
        ("MAX_USER_MESSAGE_CHARS", "dois mil"),
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


@pytest.mark.parametrize(
    "variable_name",
    (
        "OLLAMA_NUM_CTX",
        "OLLAMA_NUM_PREDICT",
        "MAX_USER_MESSAGE_CHARS",
    ),
)
@pytest.mark.parametrize("invalid_value", ("0", "-1"))
def test_rejects_non_positive_integer_environment_values(
    monkeypatch: pytest.MonkeyPatch,
    variable_name: str,
    invalid_value: str,
) -> None:
    monkeypatch.setenv(variable_name, invalid_value)

    with pytest.raises(ValueError, match=variable_name):
        Settings()
