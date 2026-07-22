from src.models import AgentContext, Intent
from src.prompts import SYSTEM_PROMPT, build_user_prompt


def test_system_prompt_explicitly_prohibits_financial_illegality():
    normalized_prompt = " ".join(SYSTEM_PROMPT.split()).casefold()

    assert "fraude" in normalized_prompt
    assert "ocultação de patrimônio" in normalized_prompt
    assert "manipulação de documentos" in normalized_prompt
    assert "evasão ilegal" in normalized_prompt
    assert "lavagem de dinheiro" in normalized_prompt
    assert "atividade financeira ilícita" in normalized_prompt


def test_user_question_is_serialized_only_once():
    user_message = "Qual é o meu saldo no período?"
    context = AgentContext(
        intent=Intent.FINANCIAL_SUMMARY,
        user_message=user_message,
    )

    prompt = build_user_prompt(user_message, context)

    assert prompt.count(user_message) == 1
    assert '"pergunta_usuario"' not in prompt
    assert "PERGUNTA_DO_USUARIO:" in prompt
