import pytest

from src.config import Settings


def test_default_limits_are_safe(monkeypatch):
    for name in ("OLLAMA_NUM_CTX", "OLLAMA_NUM_PREDICT", "MAX_USER_MESSAGE_CHARS"):
        monkeypatch.delenv(name, raising=False)
    settings = Settings()
    assert settings.ollama_num_ctx == 4096
    assert settings.ollama_num_predict == 250
    assert settings.max_user_message_chars == 2000


def test_limits_can_be_overridden(monkeypatch):
    monkeypatch.setenv("OLLAMA_NUM_CTX", "2048")
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "120")
    monkeypatch.setenv("MAX_USER_MESSAGE_CHARS", "500")
    settings = Settings()
    assert settings.ollama_num_ctx == 2048
    assert settings.ollama_num_predict == 120
    assert settings.max_user_message_chars == 500


def test_non_positive_limit_is_rejected(monkeypatch):
    monkeypatch.setenv("OLLAMA_NUM_PREDICT", "0")
    with pytest.raises(ValueError, match="maior que zero"):
        Settings()
