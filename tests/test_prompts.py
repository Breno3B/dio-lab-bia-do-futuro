from src.models import AgentContext, Intent
from src.prompts import build_user_prompt


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
    assert "\n  \"" not in prompt
    assert prompt.count("histórico") == 1
