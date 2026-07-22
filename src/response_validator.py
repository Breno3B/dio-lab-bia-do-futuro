"""Validação pós-geração com regras simples e observáveis."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from src.models import AgentContext, Intent

PROHIBITED_PATTERNS = (
    r"lucro garantido",
    r"retorno garantido",
    r"sem risco",
    r"compre agora",
    r"invista tudo",
)


@dataclass(slots=True)
class ResponseValidation:
    """Resultado da validação e conteúdo sanitizado para exibição."""

    content: str
    warnings: list[str] = field(default_factory=list)
    critical_errors: list[str] = field(default_factory=list)
    mentioned_products: list[str] = field(default_factory=list)

    @property
    def is_blocked(self) -> bool:
        return bool(self.critical_errors)


def _strip_json_fence(response: str) -> str:
    stripped = response.strip()
    fenced_match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        stripped,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return fenced_match.group(1).strip() if fenced_match else stripped


def _parse_product_response(response: str) -> tuple[str, list[str], str | None]:
    try:
        payload: Any = json.loads(_strip_json_fence(response))
    except json.JSONDecodeError:
        return "", [], "A resposta de produtos não está em JSON válido."

    if not isinstance(payload, dict):
        return "", [], "A resposta de produtos deve ser um objeto JSON."

    content = payload.get("resposta")
    mentioned_products = payload.get("produtos_mencionados")

    if not isinstance(content, str) or not content.strip():
        return "", [], "O campo 'resposta' deve conter um texto não vazio."
    if not isinstance(mentioned_products, list) or not all(
        isinstance(product, str) and product.strip()
        for product in mentioned_products
    ):
        return "", [], (
            "O campo 'produtos_mencionados' deve ser uma lista de nomes não vazios."
        )

    return content.strip(), [product.strip() for product in mentioned_products], None


def _validate_catalog(
    content: str,
    mentioned_products: list[str],
    context: AgentContext,
) -> list[str]:
    errors: list[str] = []
    allowed_for_response = {
        str(product.get("nome", "")).strip().casefold()
        for product in context.products
        if str(product.get("nome", "")).strip()
    }
    authorized_catalog = {
        product.strip().casefold()
        for product in context.authorized_product_names
        if product.strip()
    }
    mentioned_normalized = {product.casefold() for product in mentioned_products}

    unknown_catalog = mentioned_normalized - authorized_catalog
    if unknown_catalog:
        errors.append(
            "A resposta menciona produto ausente do catálogo autorizado: "
            + ", ".join(sorted(unknown_catalog))
            + "."
        )

    not_allowed_for_context = mentioned_normalized - allowed_for_response
    if not_allowed_for_context:
        errors.append(
            "A resposta menciona produto não autorizado para o contexto atual: "
            + ", ".join(sorted(not_allowed_for_context))
            + "."
        )

    content_normalized = content.casefold()
    products_found_in_text = {
        product
        for product in authorized_catalog
        if product and product in content_normalized
    }
    omitted_from_metadata = products_found_in_text - mentioned_normalized
    if omitted_from_metadata:
        errors.append(
            "Há produtos citados no texto que não foram declarados em "
            "'produtos_mencionados': "
            + ", ".join(sorted(omitted_from_metadata))
            + "."
        )

    return errors


def validate_response(response: str, context: AgentContext) -> ResponseValidation:
    """Valida a saída do LLM e classifica violações críticas."""
    raw_response = response.strip()
    if not raw_response:
        return ResponseValidation(
            content="",
            critical_errors=["A resposta gerada está vazia."],
        )

    mentioned_products: list[str] = []
    if context.intent is Intent.PRODUCT_COMPATIBILITY:
        content, mentioned_products, parse_error = _parse_product_response(raw_response)
        if parse_error:
            return ResponseValidation(
                content="",
                critical_errors=[parse_error],
            )
    else:
        content = raw_response

    result = ResponseValidation(
        content=content,
        mentioned_products=mentioned_products,
    )
    normalized = content.casefold()

    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, normalized):
            result.critical_errors.append(
                f"A resposta contém expressão de risco: '{pattern}'."
            )

    if context.intent is Intent.PRODUCT_COMPATIBILITY:
        result.critical_errors.extend(
            _validate_catalog(content, mentioned_products, context)
        )

    has_profile_conflict = any(
        "divergência" in item.casefold() or "contradição" in item.casefold()
        for item in context.inconsistencies
    )
    if (
        context.intent is Intent.PRODUCT_COMPATIBILITY
        and has_profile_conflict
        and not any(term in normalized for term in ("diverg", "contrad", "confirm"))
    ):
        result.critical_errors.append(
            "A resposta não sinalizou a divergência existente no perfil."
        )

    requires_mock_notice = (
        context.intent is Intent.PRODUCT_COMPATIBILITY
        or any(
            "mock" in restriction.casefold()
            for restriction in context.specific_restrictions
        )
    )
    if requires_mock_notice and not any(
        term in normalized for term in ("mock", "fict", "educacion")
    ):
        result.warnings.append(
            "A resposta deveria informar que os dados utilizados são mockados."
        )

    return result
