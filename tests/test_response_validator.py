import json

from src.models import AgentContext, Intent
from src.response_validator import validate_response


def _product_context(*, with_conflict: bool = False) -> AgentContext:
    return AgentContext(
        intent=Intent.PRODUCT_COMPATIBILITY,
        user_message="produto",
        products=[{"nome": "Tesouro Selic"}],
        authorized_product_names=["Tesouro Selic", "Fundo de Ações"],
        inconsistencies=(
            ["Há divergência entre perfil_investidor e aceita_risco."]
            if with_conflict
            else []
        ),
    )


def _product_response(text: str, products: list[str]) -> str:
    return json.dumps(
        {
            "resposta": text,
            "produtos_mencionados": products,
        },
        ensure_ascii=False,
    )


def test_critical_error_for_guaranteed_profit():
    context = AgentContext(
        intent=Intent.FINANCIAL_SUMMARY,
        user_message="saldo",
    )

    result = validate_response("Este produto oferece lucro garantido.", context)

    assert result.is_blocked
    assert any("lucro garantido" in error for error in result.critical_errors)


def test_does_not_require_mock_notice_for_routine_financial_summary():
    context = AgentContext(
        intent=Intent.FINANCIAL_SUMMARY,
        user_message="saldo",
        calculated_results={"saldo": 100.0},
    )

    result = validate_response("Seu saldo é R$ 100,00.", context)

    assert not result.is_blocked
    assert result.warnings == []


def test_warns_when_product_response_omits_mock_notice():
    context = _product_context()
    response = _product_response(
        "O Tesouro Selic atende aos critérios analisados.",
        ["Tesouro Selic"],
    )

    result = validate_response(response, context)

    assert not result.is_blocked
    assert any("mockados" in warning for warning in result.warnings)


def test_accepts_authorized_product_declared_in_metadata():
    context = _product_context()
    response = _product_response(
        "Nos dados mockados, o Tesouro Selic atende aos critérios analisados.",
        ["Tesouro Selic"],
    )

    result = validate_response(response, context)

    assert not result.is_blocked
    assert result.content.startswith("Nos dados mockados")
    assert result.mentioned_products == ["Tesouro Selic"]


def test_blocks_any_product_absent_from_catalog_without_hardcoded_name():
    context = _product_context()
    response = _product_response(
        "Nos dados mockados, o Fundo Premium Alpha seria uma opção.",
        ["Fundo Premium Alpha"],
    )

    result = validate_response(response, context)

    assert result.is_blocked
    assert any("ausente do catálogo" in error for error in result.critical_errors)


def test_blocks_catalog_product_not_allowed_for_current_context():
    context = _product_context()
    response = _product_response(
        "Nos dados mockados, o Fundo de Ações pode ser considerado.",
        ["Fundo de Ações"],
    )

    result = validate_response(response, context)

    assert result.is_blocked
    assert any("contexto atual" in error for error in result.critical_errors)


def test_blocks_product_response_without_structured_metadata():
    context = _product_context()

    result = validate_response("Considere o Tesouro Selic.", context)

    assert result.is_blocked
    assert any("JSON válido" in error for error in result.critical_errors)


def test_blocks_product_omitted_from_metadata():
    context = _product_context()
    response = _product_response(
        "Nos dados mockados, o Tesouro Selic atende aos critérios.",
        [],
    )

    result = validate_response(response, context)

    assert result.is_blocked
    assert any("não foram declarados" in error for error in result.critical_errors)


def test_blocks_response_that_ignores_profile_conflict():
    context = _product_context(with_conflict=True)
    context.products = []
    response = _product_response(
        "Os dados mockados foram analisados.",
        [],
    )

    result = validate_response(response, context)

    assert result.is_blocked
    assert any("divergência" in error for error in result.critical_errors)


def test_accepts_safe_response_that_explains_profile_conflict():
    context = _product_context(with_conflict=True)
    context.products = []
    response = _product_response(
        "Há divergência no perfil e é necessário confirmar a tolerância a risco. Os dados são mockados.",
        [],
    )

    result = validate_response(response, context)

    assert not result.is_blocked
