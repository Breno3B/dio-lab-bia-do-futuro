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


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def classify_intent(user_message: str) -> Intent:
    text = normalize_text(user_message)

    if not text:
        return Intent.UNKNOWN

    safe_fraud_context = _contains_any(
        text,
        (
            "o que e fraude",
            "como identificar fraude",
            "como evitar fraude",
            "como prevenir fraude",
            "como denunciar fraude",
            "denunciar tentativa de fraude",
            "fui vitima de fraude",
            "sou vitima de fraude",
            "proteger contra fraude",
            "corrigir documento",
            "atualizar documento",
            "regularizar documento",
            "corrigir renda omitida",
            "regularizar renda",
        ),
    )

    illegal_activity_patterns = (
        r"\bcomo(?: posso)? ocultar patrimonio\b",
        r"\bquero ocultar patrimonio\b",
        r"\bcomo esconder patrimonio\b",
        r"\bcomo esconder bens\b",
        r"\bcomo manipular documentos?\b",
        r"\bquero manipular documentos?\b",
        r"\bcomo adulterar documentos?\b",
        r"\bcomo falsificar documentos?\b",
        r"\bcomo criar (?:um )?documento falso\b",
        r"\bcomo criar (?:um )?comprovante falso\b",
        r"\bcomo falsificar (?:um )?comprovante\b",
        r"\bcomo fraudar (?:um )?comprovante\b",
        r"\bcomo adulterar (?:um )?extrato\b",
        r"\bcomo alterar documentos? para\b",
        r"\bcomo alterar (?:um )?extrato para\b",
        r"\bcomo omitir renda\b",
        r"\bcomo criar (?:uma )?declaracao(?: financeira)? falsa\b",
        r"\bcomo evitar fiscalizacao\b",
        r"\bcomo enganar (?:uma )?fiscalizacao\b",
        r"\bcomo enganar (?:uma )?verificacao\b",
        r"\bquero fraudar\b",
    )

    if not safe_fraud_context and _matches_any(
        text,
        illegal_activity_patterns,
    ):
        return Intent.ILLEGAL_ACTIVITY

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
            "gastei menos",
            "gastando menos",
            "menos gasto",
            "menos gastos",
            "menor categoria",
            "menor gasto",
            "menores gastos",
            "menor despesa",
            "menores despesas",
            "categoria com menor",
            "categoria de menor",
            "categoria que menos",
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
