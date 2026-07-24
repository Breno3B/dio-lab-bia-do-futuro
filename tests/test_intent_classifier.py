import pytest

from src.intent_classifier import classify_intent
from src.models import Intent


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Em que categoria estou gastando mais?", Intent.EXPENSE_ANALYSIS),
        ("Como está minha reserva de emergência?", Intent.GOAL_PROGRESS),
        ("Quais produtos combinam comigo?", Intent.PRODUCT_COMPATIBILITY),
        ("Já falei sobre Tesouro Selic?", Intent.SERVICE_HISTORY),
        ("Qual é a Selic hoje?", Intent.CURRENT_MARKET_DATA),
        ("Qual a previsão do tempo?", Intent.OUT_OF_SCOPE),
    ],
)
def test_classify_intent(message, expected):
    assert classify_intent(message) is expected


@pytest.mark.parametrize(
    "message",
    [
        "Qual foi a categoria com menor gasto?",
        "Em qual categoria eu gastei menos?",
        "Na menor categoria de gasto, qual foi o valor?",
        "Qual categoria teve a menor despesa?",
        "Com o que estou gastando menos?",
        "Qual é a categoria de menor gasto?",
        "Qual é a categoria que menos pesa nas minhas despesas?",
    ],
)
def test_classify_lowest_expense_category(message):
    assert classify_intent(message) is Intent.LOWEST_EXPENSE_CATEGORY


@pytest.mark.parametrize(
    "message",
    [
        "Em que categoria estou gastando mais?",
        "Qual foi a maior categoria de despesas?",
        "Onde está meu maior gasto?",
    ],
)
def test_lowest_expense_rule_does_not_change_largest_expense_intent(message):
    assert classify_intent(message) is Intent.EXPENSE_ANALYSIS
