"""Validação pós-geração com regras simples e observáveis."""

from __future__ import annotations

import re

from src.models import AgentContext

PROHIBITED_PATTERNS = (
    r"lucro garantido",
    r"retorno garantido",
    r"sem risco",
    r"compre agora",
    r"invista tudo",
)


def validate_response(response: str, context: AgentContext) -> list[str]:
    warnings: list[str] = []
    normalized = response.casefold().strip()
    if not normalized:
        return ["A resposta gerada está vazia."]

    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, normalized):
            warnings.append(f"A resposta contém expressão de risco: '{pattern}'.")

    allowed_products = {str(product.get("nome", "")).casefold() for product in context.products}
    if allowed_products:
        # O validador apenas verifica nomes do catálogo carregado no contexto.
        if "bitcoin" in normalized and "bitcoin" not in allowed_products:
            warnings.append("A resposta menciona produto ausente do catálogo autorizado.")

    has_profile_conflict = any("divergência" in item.casefold() for item in context.inconsistencies)
    if has_profile_conflict and not any(term in normalized for term in ("diverg", "contrad", "confirm")):
        warnings.append("A resposta não sinalizou a divergência existente no perfil.")

    presents_financial_data = bool(context.calculated_results or context.products)
    if presents_financial_data and not any(term in normalized for term in ("mock", "fict", "educacion")):
        warnings.append("A resposta apresenta dados financeiros sem avisar que a base é mockada.")

    return warnings
