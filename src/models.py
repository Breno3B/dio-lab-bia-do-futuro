"""Modelos de dados internos da ClaraMente."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import pandas as pd


class Intent(StrEnum):
    FINANCIAL_SUMMARY = "financial_summary"
    EXPENSE_ANALYSIS = "expense_analysis"
    LOWEST_EXPENSE_CATEGORY = "lowest_expense_category"
    PERIOD_COMPARISON = "period_comparison"
    GOAL_PROGRESS = "goal_progress"
    PRODUCT_COMPATIBILITY = "product_compatibility"
    SERVICE_HISTORY = "service_history"
    CURRENT_MARKET_DATA = "current_market_data"
    OUT_OF_SCOPE = "out_of_scope"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class KnowledgeBase:
    transactions: pd.DataFrame
    service_history: pd.DataFrame
    investor_profile: dict[str, Any]
    financial_products: list[dict[str, Any]]


@dataclass(slots=True)
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def extend(self, other: "ValidationReport") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


@dataclass(slots=True)
class AgentContext:
    intent: Intent
    user_message: str
    sources: list[str] = field(default_factory=list)
    period: dict[str, str] | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    calculated_results: dict[str, Any] = field(default_factory=dict)
    relevant_profile: dict[str, Any] = field(default_factory=dict)
    products: list[dict[str, Any]] = field(default_factory=list)
    authorized_product_names: list[str] = field(default_factory=list)
    relevant_history: list[dict[str, Any]] = field(default_factory=list)
    inconsistencies: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    specific_restrictions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intencao": self.intent.value,
            "pergunta_usuario": self.user_message,
            "fontes_consultadas": self.sources,
            "periodo_analisado": self.period,
            "filtros_aplicados": self.filters,
            "resultados_calculados": self.calculated_results,
            "dados_relevantes_perfil": self.relevant_profile,
            "produtos_encontrados_catalogo": self.products,
            "nomes_produtos_autorizados": self.authorized_product_names,
            "historico_relevante": self.relevant_history,
            "inconsistencias": self.inconsistencies,
            "dados_ausentes": self.missing_data,
            "limitacoes": self.limitations,
            "restricoes_especificas": self.specific_restrictions,
        }


@dataclass(slots=True)
class AgentResponse:
    content: str
    intent: Intent
    context: AgentContext
    warnings: list[str] = field(default_factory=list)
    performance_metrics: dict[str, Any] = field(default_factory=dict)
