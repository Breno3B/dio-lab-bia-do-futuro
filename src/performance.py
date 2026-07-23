"""Instrumentação leve de performance para o fluxo da ClaraMente."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import perf_counter
from typing import Any


@dataclass(slots=True)
class PerformanceMetrics:
    """Métricas observáveis de uma única resposta."""

    total_ms: float = 0.0
    validation_ms: float = 0.0
    classification_ms: float = 0.0
    context_ms: float = 0.0
    deterministic_ms: float = 0.0
    prompt_ms: float = 0.0
    llm_ms: float = 0.0
    response_validation_ms: float = 0.0
    used_llm: bool = False
    input_chars: int = 0
    output_chars: int = 0
    prompt_eval_count: int | None = None
    eval_count: int | None = None
    prompt_eval_duration_ms: float | None = None
    eval_duration_ms: float | None = None
    load_duration_ms: float | None = None
    tokens_per_second: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def elapsed_ms(start: float) -> float:
    """Converte o intervalo desde ``start`` para milissegundos."""

    return round((perf_counter() - start) * 1000, 2)
