from copy import deepcopy

from src.context_builder import build_context
from src.data_validator import validate_knowledge_base
from src.models import Intent, KnowledgeBase


def test_expense_context_uses_only_transactions(knowledge_base):
    report = validate_knowledge_base(knowledge_base, raise_on_error=False)

    context = build_context(
        Intent.EXPENSE_ANALYSIS,
        "gastos",
        knowledge_base,
        report,
    )

    assert context.sources == ["data/transacoes.csv"]
    assert context.filters == {"tipo": "saida"}
    assert context.calculated_results["maior_categoria"]["categoria"] == "moradia"


def test_product_context_blocks_selection_when_profile_conflicts(knowledge_base):
    report = validate_knowledge_base(knowledge_base, raise_on_error=False)

    context = build_context(
        Intent.PRODUCT_COMPATIBILITY,
        "produtos",
        knowledge_base,
        report,
    )

    assert context.products == []
    assert context.authorized_product_names == ["Tesouro Selic", "Fundo de Ações"]
    assert any("divergência" in item for item in context.inconsistencies)
    assert any("confirmar" in item for item in context.missing_data)


def test_product_context_selects_products_after_profile_is_consistent(knowledge_base):
    profile = deepcopy(knowledge_base.investor_profile)
    profile["perfil_investidor"] = "conservador"
    consistent_base = KnowledgeBase(
        transactions=knowledge_base.transactions,
        service_history=knowledge_base.service_history,
        investor_profile=profile,
        financial_products=knowledge_base.financial_products,
    )
    report = validate_knowledge_base(consistent_base, raise_on_error=False)

    context = build_context(
        Intent.PRODUCT_COMPATIBILITY,
        "produtos",
        consistent_base,
        report,
    )

    assert [product["nome"] for product in context.products] == ["Tesouro Selic"]


def test_financial_summary_does_not_require_repeated_mock_notice(knowledge_base):
    report = validate_knowledge_base(knowledge_base, raise_on_error=False)

    context = build_context(
        Intent.FINANCIAL_SUMMARY,
        "saldo",
        knowledge_base,
        report,
    )

    assert context.period["descricao"] == "01/10/2025 a 10/10/2025"
    assert context.limitations == []
    assert not any(
        "mock" in restriction.casefold()
        for restriction in context.specific_restrictions
    )


def test_product_context_keeps_mock_notice(knowledge_base):
    report = validate_knowledge_base(knowledge_base, raise_on_error=False)

    context = build_context(
        Intent.PRODUCT_COMPATIBILITY,
        "produtos",
        knowledge_base,
        report,
    )

    assert any("mock" in item.casefold() for item in context.limitations)
    assert any(
        "mock" in item.casefold()
        for item in context.specific_restrictions
    )
