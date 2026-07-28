"""Orquestração do fluxo completo da ClaraMente."""

from __future__ import annotations

from time import perf_counter
from typing import Any, Protocol

from src.config import SETTINGS, Settings
from src.context_builder import build_context
from src.data_validator import validate_knowledge_base
from src.deterministic_responses import build_deterministic_response
from src.intent_classifier import classify_intent, normalize_text
from src.models import AgentContext, AgentResponse, Intent, KnowledgeBase
from src.performance import PerformanceMetrics, elapsed_ms
from src.prompts import SYSTEM_PROMPT, build_user_prompt
from src.response_validator import validate_response

SAFE_BLOCKED_RESPONSE = (
    "Não consegui apresentar a resposta gerada porque ela violou regras de "
    "segurança da ClaraMente. Reformule a pergunta ou revise os dados. "
    "Os dados deste projeto são mockados e têm finalidade educacional."
)

SAFE_PRODUCT_FALLBACK_RESPONSE = (
    "Não posso apresentar produtos para esta solicitação. O catálogo é "
    "fechado e os dados disponíveis não permitem avaliar opções com "
    "segurança neste contexto. Também existe uma divergência no perfil "
    "que precisa ser confirmada antes de prosseguir. Os dados são mockados "
    "e têm finalidade educacional."
)

PRODUCT_FALLBACK_WARNING = (
    "A resposta gerada para produtos não passou pelas validações ou a "
    "solicitação exigiu o fallback seguro."
)

HISTORY_FALLBACK_WARNING = (
    "A resposta gerada para o histórico não passou pelas validações e foi "
    "substituída por uma resposta segura."
)


class LLMClientProtocol(Protocol):
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        json_format: bool = False,
    ) -> str: ...


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


def _requires_product_fallback(user_message: str) -> bool:
    normalized = normalize_text(user_message)
    adversarial_patterns = (
        "ignore o catalogo",
        "desconsidere o catalogo",
        "mesmo que nao esteja",
        "mesmo que ele nao esteja",
        "mesmo que nao exista",
        "mesmo que ele nao exista",
        "invente",
        "lucro garantido",
        "retorno garantido",
        "sem risco",
    )
    return any(
        pattern in normalized
        for pattern in adversarial_patterns
    )


def _history_entry_text(entry: dict[str, Any]) -> str | None:
    date_value = (
        entry.get("data")
        or entry.get("date")
        or entry.get("data_atendimento")
    )
    topic = entry.get("tema") or entry.get("assunto")
    summary = entry.get("resumo") or entry.get("summary")

    parts = [
        str(value).strip()
        for value in (date_value, topic, summary)
        if value is not None and str(value).strip()
    ]
    return " — ".join(parts) if parts else None


def _build_history_fallback(context: AgentContext) -> str:
    entries = getattr(context, "relevant_history", [])
    if not entries:
        return (
            "Não foram encontrados atendimentos anteriores relacionados à "
            "consulta. O histórico disponível confirma apenas assuntos "
            "registrados, não movimentações financeiras."
        )

    formatted_entries = [
        text
        for entry in entries[:3]
        if isinstance(entry, dict)
        and (text := _history_entry_text(entry))
    ]
    if not formatted_entries:
        return (
            "Há registros de atendimento relacionados à consulta, mas os "
            "dados disponíveis não permitem apresentar detalhes com "
            "segurança. O histórico confirma apenas os assuntos tratados."
        )

    return (
        "Foram encontrados estes registros relacionados: "
        + "; ".join(formatted_entries)
        + ". O histórico confirma apenas os assuntos tratados, não "
        "movimentações financeiras."
    )


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
    raw_content = llm_client.generate(
        SYSTEM_PROMPT,
        user_prompt,
        json_format=intent is Intent.PRODUCT_COMPATIBILITY,
    )
    metrics.llm_ms = elapsed_ms(step_start)
    metrics.used_llm = True
    metrics.output_chars = len(raw_content)
    _merge_llm_metrics(metrics, llm_client)

    step_start = perf_counter()
    validation = validate_response(raw_content, context)
    metrics.response_validation_ms = elapsed_ms(step_start)
    metrics.total_ms = elapsed_ms(total_start)

    if (
        intent is Intent.PRODUCT_COMPATIBILITY
        and (
            validation.is_blocked
            or _requires_product_fallback(cleaned_message)
        )
    ):
        return AgentResponse(
            content=SAFE_PRODUCT_FALLBACK_RESPONSE,
            intent=intent,
            context=context,
            warnings=[
                *validation.warnings,
                PRODUCT_FALLBACK_WARNING,
            ],
            performance_metrics=metrics.to_dict(),
        )

    if (
        intent is Intent.SERVICE_HISTORY
        and validation.is_blocked
    ):
        return AgentResponse(
            content=_build_history_fallback(context),
            intent=intent,
            context=context,
            warnings=[
                *validation.warnings,
                HISTORY_FALLBACK_WARNING,
            ],
            performance_metrics=metrics.to_dict(),
        )

    if validation.is_blocked:
        return AgentResponse(
            content=SAFE_BLOCKED_RESPONSE,
            intent=intent,
            context=context,
            warnings=[
                *validation.warnings,
                *(
                    f"Resposta bloqueada: {error}"
                    for error in validation.critical_errors
                ),
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
