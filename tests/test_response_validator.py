from src.models import AgentContext, Intent
from src.response_validator import validate_response


def test_warns_about_guaranteed_profit():
    context = AgentContext(intent=Intent.PRODUCT_COMPATIBILITY, user_message="produto")
    warnings = validate_response("Este produto oferece lucro garantido.", context)
    assert any("lucro garantido" in warning for warning in warnings)


def test_warns_when_mock_notice_is_missing():
    context = AgentContext(
        intent=Intent.FINANCIAL_SUMMARY,
        user_message="saldo",
        calculated_results={"saldo": 100.0},
    )
    warnings = validate_response("Seu saldo é R$ 100,00.", context)
    assert any("mockada" in warning for warning in warnings)
