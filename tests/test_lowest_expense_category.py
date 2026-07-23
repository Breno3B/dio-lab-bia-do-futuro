from __future__ import annotations

import pandas as pd
import pytest

from src.analytics import calculate_expenses_by_category
from src.context_builder import build_context
from src.deterministic_responses import build_deterministic_response
from src.intent_classifier import classify_intent
from src.models import Intent, KnowledgeBase


@pytest.fixture
def knowledge_base() -> KnowledgeBase:
    transactions = pd.DataFrame(
        [
            {
                "data": pd.Timestamp("2025-10-01"),
                "descricao": "Salário",
                "categoria": "receita",
                "valor": 5000.0,
                "tipo": "entrada",
            },
            {
                "data": pd.Timestamp("2025-10-02"),
                "descricao": "Aluguel",
                "categoria": "moradia",
                "valor": 1200.0,
                "tipo": "saida",
            },
            {
                "data": pd.Timestamp("2025-10-03"),
                "descricao": "Supermercado",
                "categoria": "alimentacao",
                "valor": 450.0,
                "tipo": "saida",
            },
            {
                "data": pd.Timestamp("2025-10-10"),
                "descricao": "Restaurante",
                "categoria": "alimentacao",
                "valor": 120.0,
                "tipo": "saida",
            },
        ]
    )
    return KnowledgeBase(
        transactions=transactions,
        service_history=pd.DataFrame(
            columns=["data", "canal", "tema", "resumo", "resolvido"]
        ),
        investor_profile={},
        financial_products=[],
    )


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Com o que eu mais gasto?", Intent.EXPENSE_ANALYSIS),
        ("Em que categoria estou gastando mais?", Intent.EXPENSE_ANALYSIS),
        ("Com o que eu menos gasto?", Intent.LOWEST_EXPENSE_CATEGORY),
        ("Em que categoria estou gastando menos?", Intent.LOWEST_EXPENSE_CATEGORY),
        ("Qual é a minha menor despesa por categoria?", Intent.LOWEST_EXPENSE_CATEGORY),
    ],
)
def test_classifies_maximum_and_minimum_expense_questions(message, expected):
    assert classify_intent(message) is expected


def test_calculates_lowest_expense_category(knowledge_base):
    result = calculate_expenses_by_category(knowledge_base.transactions)

    assert result["maior_categoria"] == {
        "categoria": "moradia",
        "valor": 1200.0,
        "participacao_percentual": 67.8,
    }
    assert result["menor_categoria"] == {
        "categoria": "alimentacao",
        "valor": 570.0,
        "participacao_percentual": 32.2,
    }


def test_builds_lowest_expense_context(knowledge_base):
    context = build_context(
        Intent.LOWEST_EXPENSE_CATEGORY,
        "Com o que eu menos gasto?",
        knowledge_base,
    )

    assert context.sources == ["data/transacoes.csv"]
    assert context.filters == {"tipo": "saida"}
    assert context.calculated_results["menor_categoria"]["categoria"] == "alimentacao"


def test_lowest_expense_response_does_not_use_largest_category(knowledge_base):
    context = build_context(
        Intent.LOWEST_EXPENSE_CATEGORY,
        "Com o que eu menos gasto?",
        knowledge_base,
    )

    response = build_deterministic_response(context)

    assert response is not None
    assert "menor categoria de gastos" in response
    assert "**alimentacao**" in response
    assert "R$ 570,00" in response
    assert "32,20%" in response
    assert "**moradia**" not in response
