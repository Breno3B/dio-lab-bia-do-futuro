import pytest

from src.exceptions import LLMUnavailableError
from src.llm_client import OllamaLLMClient


class FailingOllamaClient:
    def chat(self, **kwargs):
        raise RuntimeError(
            "connection failed at http://internal-host:11434/api/chat"
        )


class RecordingOllamaClient:
    def __init__(self) -> None:
        self.chat_arguments = {}

    def chat(self, **kwargs):
        self.chat_arguments = kwargs
        return {
            "message": {"content": '{"resposta": "ok"}'},
            "prompt_eval_count": 10,
            "eval_count": 5,
            "eval_duration": 1_000_000_000,
        }


def test_generate_does_not_expose_internal_exception(
    monkeypatch,
    settings,
):
    client = OllamaLLMClient(settings)
    monkeypatch.setattr(client, "is_available", lambda: True)
    monkeypatch.setattr(client, "_client", lambda: FailingOllamaClient())

    with pytest.raises(LLMUnavailableError) as exc_info:
        client.generate("system", "user")

    assert str(exc_info.value) == "Não foi possível consultar o modelo local."
    assert "internal-host" not in str(exc_info.value)
    assert "api/chat" not in str(exc_info.value)


def test_generate_does_not_request_json_by_default(
    monkeypatch,
    settings,
):
    ollama_client = RecordingOllamaClient()
    client = OllamaLLMClient(settings)

    monkeypatch.setattr(client, "is_available", lambda: True)
    monkeypatch.setattr(client, "_client", lambda: ollama_client)

    client.generate("system", "user")

    assert "format" not in ollama_client.chat_arguments
    assert ollama_client.chat_arguments["think"] is False


def test_generate_requests_json_when_enabled(
    monkeypatch,
    settings,
):
    ollama_client = RecordingOllamaClient()
    client = OllamaLLMClient(settings)

    monkeypatch.setattr(client, "is_available", lambda: True)
    monkeypatch.setattr(client, "_client", lambda: ollama_client)

    client.generate("system", "user", json_format=True)

    assert ollama_client.chat_arguments["format"] == "json"
    assert ollama_client.chat_arguments["think"] is False


def test_stream_does_not_expose_internal_exception(
    monkeypatch,
    settings,
):
    client = OllamaLLMClient(settings)
    monkeypatch.setattr(client, "is_available", lambda: True)
    monkeypatch.setattr(client, "_client", lambda: FailingOllamaClient())

    with pytest.raises(LLMUnavailableError) as exc_info:
        list(client.stream("system", "user"))

    assert str(exc_info.value) == "Não foi possível consultar o modelo local."
    assert "internal-host" not in str(exc_info.value)
    assert "api/chat" not in str(exc_info.value)
