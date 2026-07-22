import pytest

from src.exceptions import LLMUnavailableError
from src.llm_client import OllamaLLMClient


class FailingOllamaClient:
    def chat(self, **kwargs):
        raise RuntimeError(
            "connection failed at http://internal-host:11434/api/chat"
        )


def test_generate_does_not_expose_internal_exception(monkeypatch, settings):
    client = OllamaLLMClient(settings)
    monkeypatch.setattr(client, "is_available", lambda: True)
    monkeypatch.setattr(client, "_client", lambda: FailingOllamaClient())

    with pytest.raises(LLMUnavailableError) as exc_info:
        client.generate("system", "user")

    assert str(exc_info.value) == "Não foi possível consultar o modelo local."
    assert "internal-host" not in str(exc_info.value)
    assert "api/chat" not in str(exc_info.value)


def test_stream_does_not_expose_internal_exception(monkeypatch, settings):
    client = OllamaLLMClient(settings)
    monkeypatch.setattr(client, "is_available", lambda: True)
    monkeypatch.setattr(client, "_client", lambda: FailingOllamaClient())

    with pytest.raises(LLMUnavailableError) as exc_info:
        list(client.stream("system", "user"))

    assert str(exc_info.value) == "Não foi possível consultar o modelo local."
    assert "internal-host" not in str(exc_info.value)
    assert "api/chat" not in str(exc_info.value)
