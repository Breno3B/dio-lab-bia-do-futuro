from src.analytics import (
    calculate_expenses_by_category,
    calculate_goal_progress,
    calculate_period_summary,
    find_compatible_products,
)


def test_period_summary(knowledge_base):
    result = calculate_period_summary(knowledge_base.transactions)
    assert result["total_entradas"] == 5000.0
    assert result["total_saidas"] == 1770.0
    assert result["saldo"] == 3230.0


def test_expenses_by_category(knowledge_base):
    result = calculate_expenses_by_category(knowledge_base.transactions)
    assert result["maior_categoria"]["categoria"] == "moradia"
    assert result["maior_categoria"]["valor"] == 1200.0


def test_goal_progress(knowledge_base):
    result = calculate_goal_progress(knowledge_base.investor_profile)
    assert result[0]["progresso_percentual"] == 66.67


def test_products_respect_explicit_risk_tolerance(knowledge_base):
    result = find_compatible_products(
        knowledge_base.investor_profile, knowledge_base.financial_products
    )
    assert [product["nome"] for product in result] == ["Tesouro Selic"]
