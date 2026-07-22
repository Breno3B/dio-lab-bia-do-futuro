from copy import deepcopy

from src.analytics import (
    available_period,
    calculate_expenses_by_category,
    calculate_goal_progress,
    calculate_period_summary,
    find_compatible_products,
)




def test_available_period_uses_brazilian_date_format(knowledge_base):
    result = available_period(knowledge_base.transactions)

    assert result == {
        "inicio": "01/10/2025",
        "fim": "10/10/2025",
        "descricao": "01/10/2025 a 10/10/2025",
    }


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


def test_goal_progress_preserves_missing_value_instead_of_zero(knowledge_base):
    profile = deepcopy(knowledge_base.investor_profile)
    profile.pop("reserva_emergencia_atual")

    result = calculate_goal_progress(profile)

    assert result[0]["valor_atual"] is None
    assert result[0]["valor_restante"] is None
    assert result[0]["progresso_percentual"] is None
    assert "não foi informado" in result[0]["observacao"]


def test_non_reserve_goal_uses_missing_value_instead_of_zero(knowledge_base):
    profile = deepcopy(knowledge_base.investor_profile)
    profile["metas"] = [
        {
            "meta": "Comprar um imóvel",
            "valor_necessario": 100000.0,
            "prazo": "2030-01",
        }
    ]

    result = calculate_goal_progress(profile)

    assert result[0]["valor_atual"] is None
    assert result[0]["progresso_percentual"] is None
    assert "não informa" in result[0]["observacao"]


def test_products_respect_explicit_risk_tolerance(knowledge_base):
    result = find_compatible_products(
        knowledge_base.investor_profile,
        knowledge_base.financial_products,
    )

    assert [product["nome"] for product in result] == ["Tesouro Selic"]
