from src.context_builder import build_context
from src.data_validator import validate_knowledge_base
from src.models import Intent


def test_expense_context_uses_only_transactions(knowledge_base):
    report = validate_knowledge_base(knowledge_base, raise_on_error=False)
    context = build_context(Intent.EXPENSE_ANALYSIS, "gastos", knowledge_base, report)
    assert context.sources == ["data/transacoes.csv"]
    assert context.filters == {"tipo": "saida"}
    assert context.calculated_results["maior_categoria"]["categoria"] == "moradia"


def test_product_context_carries_profile_conflict(knowledge_base):
    report = validate_knowledge_base(knowledge_base, raise_on_error=False)
    context = build_context(Intent.PRODUCT_COMPATIBILITY, "produtos", knowledge_base, report)
    assert context.products[0]["nome"] == "Tesouro Selic"
    assert any("divergência" in item for item in context.inconsistencies)
