from src.models import AgentContext, Intent
from src.prompts import SYSTEM_PROMPT, build_user_prompt


def test_prompt_is_compact_and_removes_empty_fields():
    context = AgentContext(
        intent=Intent.SERVICE_HISTORY,
        user_message="histórico",
        relevant_history=[{"tema": "Metas"}],
    )

    prompt = build_user_prompt("histórico", context)

    assert '"fontes_consultadas"' not in prompt
    assert '"filtros_aplicados"' not in prompt
    assert '"historico_relevante":[{"tema":"Metas"}]' in prompt
    assert '\n  "' not in prompt
    assert prompt.count("histórico") == 1


def test_product_prompt_requires_non_empty_response():
    normalized_prompt = " ".join(SYSTEM_PROMPT.split())

    assert 'O campo "resposta" nunca pode ser vazio.' in normalized_prompt
    assert (
        'use uma lista vazia em "produtos_mencionados"'
        in normalized_prompt
    )
    assert (
        'explique o motivo no campo "resposta"'
        in normalized_prompt
    )
