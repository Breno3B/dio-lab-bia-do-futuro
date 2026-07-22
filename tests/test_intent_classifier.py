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
