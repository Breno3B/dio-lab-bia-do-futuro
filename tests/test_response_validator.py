import json

from src.models import AgentContext, Intent
from src.response_validator import validate_response


def test_accepts_numeric_value_grounded_in_calculated_results():
    context = AgentContext(
        intent=Intent.SERVICE_HISTORY,
        user_message="teste",
        calculated_results={"saldo": 3230.0, "participacao": 67.8},
    )
    result = validate_response("Saldo de R$ 3.230,00 e participação de 67,8%.", context)
    assert not result.is_blocked


def test_blocks_numeric_value_not_grounded_in_context():
    context = AgentContext(
        intent=Intent.SERVICE_HISTORY,
        user_message="teste",
        calculated_results={"saldo": 3230.0},
    )
    result = validate_response("O saldo é R$ 3.250,00.", context)
    assert result.is_blocked
    assert any("não fundamentado" in item for item in result.critical_errors)


def test_product_percentage_from_catalog_is_allowed():
    context = AgentContext(
        intent=Intent.PRODUCT_COMPATIBILITY,
        user_message="produto",
        products=[{"nome": "Tesouro Selic", "rentabilidade": "100% da Selic"}],
        authorized_product_names=["Tesouro Selic"],
    )
    response = json.dumps(
        {
            "resposta": "Nos dados mockados, o Tesouro Selic informa 100% da Selic.",
            "produtos_mencionados": ["Tesouro Selic"],
        },
        ensure_ascii=False,
    )
    result = validate_response(response, context)
    assert not result.is_blocked
