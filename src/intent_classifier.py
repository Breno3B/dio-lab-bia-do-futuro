"""Classificação simples e reproduzível da intenção do usuário."""

from __future__ import annotations

import re
import unicodedata

from src.models import Intent


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    without_accents = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", without_accents).strip()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def classify_intent(user_message: str) -> Intent:
    text = normalize_text(user_message)

    if not text:
        return Intent.UNKNOWN

    if _contains_any(
        text,
        ("tempo amanha", "previsao do tempo", "receita culinaria", "placar", "futebol"),
    ):
        return Intent.OUT_OF_SCOPE

    if _contains_any(
        text,
        ("selic hoje", "cotacao hoje", "preco hoje", "taxa atual", "mercado hoje"),
    ):
        return Intent.CURRENT_MARKET_DATA

    if _contains_any(
        text,
        ("ja falei", "atendimento anterior", "historico", "conversa anterior"),
    ):
        return Intent.SERVICE_HISTORY

    if _contains_any(
        text,
        ("meta", "reserva de emergencia", "progresso", "quanto falta"),
    ):
        return Intent.GOAL_PROGRESS

    if _contains_any(
        text,
        ("produto", "investir", "investimento", "cdb", "tesouro", "fundo", "lci", "lca"),
    ):
        return Intent.PRODUCT_COMPATIBILITY

    if _contains_any(
        text,
        ("mes anterior", "comparar", "aumentaram", "diminuiram", "variacao"),
    ):
        return Intent.PERIOD_COMPARISON

    # Deve vir antes da regra genérica de despesas, pois "menos gasto"
    # também contém a palavra "gasto".
    if _contains_any(
        text,
        (
            "gasto menos",
            "gastos menos",
            "menos gasto",
            "menos gastos",
            "gastando menos",
            "menor gasto",
            "menores gastos",
            "menor despesa",
            "menores despesas",
            "categoria com menor",
            "categoria menos",
        ),
    ):
        return Intent.LOWEST_EXPENSE_CATEGORY

    if _contains_any(
        text,
        (
            "categoria",
            "gastando mais",
            "gasto mais",
            "mais gasto",
            "maior gasto",
            "gasto",
            "despesa",
            "alimentacao",
            "moradia",
        ),
    ):
        return Intent.EXPENSE_ANALYSIS

    if _contains_any(
        text,
        ("resumo", "saldo", "entradas", "saidas", "saude financeira"),
    ):
        return Intent.FINANCIAL_SUMMARY

    return Intent.UNKNOWN
