"""Orquestração do fluxo completo da ClaraMente."""

from __future__ import annotations

from time import perf_counter
from typing import Protocol

from src.config import SETTINGS, Settings
from src.context_builder import build_context
from src.data_validator import validate_knowledge_base
from src.deterministic_responses import build_deterministic_response
from src.intent_classifier import classify_intent
from src.models import AgentResponse, KnowledgeBase
from src.performance import PerformanceMetrics, elapsed_ms
from src.prompts import SYSTEM_PROMPT, build_user_prompt
from src.response_validator import validate_response

SAFE_BLOCKED_RESPONSE = (
    "Não consegui apresentar a resposta gerada porque ela violou regras de "
    "segurança da ClaraMente. Reformule a pergunta ou revise os dados. "
    "Os dados deste projeto são mockados e têm finalidade educacional."
)


class LLMClientProtocol(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


def _merge_llm_metrics(
    metrics: PerformanceMetrics,
    llm_client: LLMClientProtocol,
) -> None:
    raw_metrics = getattr(llm_client, "last_metrics", {})
    if not isinstance(raw_metrics, dict):
        return

    for field_name in (
        "prompt_eval_count",
        "eval_count",
        "prompt_eval_duration_ms",
        "eval_duration_ms",
        "load_duration_ms",
        "tokens_per_second",
    ):
        if field_name in raw_metrics:
            setattr(metrics, field_name, raw_metrics[field_name])


def answer_user_message(
    user_message: str,
    knowledge_base: KnowledgeBase,
    llm_client: LLMClientProtocol,
    settings: Settings = SETTINGS,
) -> AgentResponse:
    total_start = perf_counter()
    metrics = PerformanceMetrics()

    cleaned_message = user_message.strip()
    if not cleaned_message:
        raise ValueError("A mensagem do usuário não pode estar vazia.")
    if len(cleaned_message) > settings.max_user_message_chars:
        raise ValueError(
            "A mensagem excede o limite de "
            f"{settings.max_user_message_chars} caracteres."
        )

    step_start = perf_counter()
    validation_report = validate_knowledge_base(
        knowledge_base,
        raise_on_error=True,
    )
    metrics.validation_ms = elapsed_ms(step_start)

    step_start = perf_counter()
    intent = classify_intent(cleaned_message)
    metrics.classification_ms = elapsed_ms(step_start)

    step_start = perf_counter()
    context = build_context(
        intent,
        cleaned_message,
        knowledge_base,
        validation_report,
    )
    metrics.context_ms = elapsed_ms(step_start)

    step_start = perf_counter()
    deterministic_content = build_deterministic_response(context)
    metrics.deterministic_ms = elapsed_ms(step_start)

    if deterministic_content is not None:
        metrics.used_llm = False
        metrics.input_chars = len(cleaned_message)
        metrics.output_chars = len(deterministic_content)
        metrics.total_ms = elapsed_ms(total_start)
        return AgentResponse(
            content=deterministic_content,
            intent=intent,
            context=context,
            performance_metrics=metrics.to_dict(),
        )

    step_start = perf_counter()
    user_prompt = build_user_prompt(cleaned_message, context)
    metrics.prompt_ms = elapsed_ms(step_start)
    metrics.input_chars = len(SYSTEM_PROMPT) + len(user_prompt)

    step_start = perf_counter()
    raw_content = llm_client.generate(SYSTEM_PROMPT, user_prompt)
    metrics.llm_ms = elapsed_ms(step_start)
    metrics.used_llm = True
    metrics.output_chars = len(raw_content)
    _merge_llm_metrics(metrics, llm_client)

    step_start = perf_counter()
    validation = validate_response(raw_content, context)
    metrics.response_validation_ms = elapsed_ms(step_start)
    metrics.total_ms = elapsed_ms(total_start)

    if validation.is_blocked:
        return AgentResponse(
            content=SAFE_BLOCKED_RESPONSE,
            intent=intent,
            context=context,
            warnings=[
                *validation.warnings,
                *(f"Resposta bloqueada: {error}" for error in validation.critical_errors),
            ],
            performance_metrics=metrics.to_dict(),
        )

    return AgentResponse(
        content=validation.content,
        intent=intent,
        context=context,
        warnings=validation.warnings,
        performance_metrics=metrics.to_dict(),
    )
