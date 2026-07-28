import pytest

from src.orchestrator import (
    PRODUCT_FALLBACK_WARNING,
    SAFE_BLOCKED_RESPONSE,
    SAFE_PRODUCT_FALLBACK_RESPONSE,
    answer_user_message,
)


class TrackingLLMClient:
    def __init__(self, response: str = "Resposta sem números.") -> None:
        self.called = False
        self.response = response
        self.json_format = None
        self.last_metrics = {
            "prompt_eval_count": 100,
            "eval_count": 20,
            "tokens_per_second": 5.0,
        }

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        json_format: bool = False,
    ) -> str:
        self.called = True
        self.json_format = json_format
        return self.response


def test_simple_summary_uses_deterministic_response(
    knowledge_base,
    settings,
):
    client = TrackingLLMClient()

    response = answer_user_message(
        "Qual é o meu saldo?",
        knowledge_base,
        client,
        settings,
    )

    assert not client.called
    assert response.content.startswith("Resumo:")
    assert "R$ 3.230,00" in response.content
    assert response.performance_metrics["used_llm"] is False
    assert response.performance_metrics["total_ms"] >= 0


def test_service_history_uses_text_response_and_records_metrics(
    knowledge_base,
    settings,
):
    client = TrackingLLMClient(
        "O histórico informa que o tema foi discutido."
    )

    response = answer_user_message(
        "Já falei sobre Tesouro Selic?",
        knowledge_base,
        client,
        settings,
    )

    assert client.called
    assert client.json_format is False
    assert response.performance_metrics["used_llm"] is True
    assert response.performance_metrics["eval_count"] == 20
    assert response.performance_metrics["llm_ms"] >= 0


def test_product_query_requests_json_response(
    knowledge_base,
    settings,
):
    client = TrackingLLMClient(
        '{"resposta": "Os dados são fictícios e existe uma divergência '
        'no perfil que precisa ser confirmada antes de avaliar produtos.", '
        '"produtos_mencionados": []}'
    )

    response = answer_user_message(
        "Quais produtos combinam com meu perfil?",
        knowledge_base,
        client,
        settings,
    )

    assert client.called
    assert client.json_format is True
    assert response.performance_metrics["used_llm"] is True
    assert response.content != SAFE_PRODUCT_FALLBACK_RESPONSE
    assert not response.warnings


def test_invalid_product_response_uses_safe_fallback(
    knowledge_base,
    settings,
):
    client = TrackingLLMClient(
        '{"resposta": "Considere um produto inexistente.", '
        '"produtos_mencionados": ["Produto inexistente"]}'
    )

    response = answer_user_message(
        "Inclua um produto que não esteja no catálogo.",
        knowledge_base,
        client,
        settings,
    )

    assert client.called
    assert client.json_format is True
    assert response.content == SAFE_PRODUCT_FALLBACK_RESPONSE
    assert PRODUCT_FALLBACK_WARNING in response.warnings
    assert not any(
        warning.startswith("Resposta bloqueada:")
        for warning in response.warnings
    )
    assert "Produto inexistente" not in response.content


def test_non_product_block_keeps_default_safe_response(
    knowledge_base,
    settings,
):
    client = TrackingLLMClient(
        "O atendimento indica um saldo de R$ 9.999,99."
    )

    response = answer_user_message(
        "Já falei anteriormente sobre saldo?",
        knowledge_base,
        client,
        settings,
    )

    assert response.content == SAFE_BLOCKED_RESPONSE
    assert any(
        warning.startswith("Resposta bloqueada:")
        for warning in response.warnings
    )


def test_rejects_message_above_configured_limit(
    knowledge_base,
    settings,
):
    client = TrackingLLMClient()
    tiny_settings = settings.__class__(
        data_dir=settings.data_dir,
        max_user_message_chars=10,
    )

    with pytest.raises(ValueError, match="excede o limite"):
        answer_user_message(
            "mensagem muito longa",
            knowledge_base,
            client,
            tiny_settings,
        )


def test_numeric_hallucination_is_blocked_for_llm_path(
    knowledge_base,
    settings,
):
    client = TrackingLLMClient(
        "O atendimento indica um saldo de R$ 9.999,99."
    )

    response = answer_user_message(
        "Já falei anteriormente sobre saldo?",
        knowledge_base,
        client,
        settings,
    )

    assert any(
        "não fundamentado" in warning
        for warning in response.warnings
    )
