"""Orquestração do fluxo completo da ClaraMente."""

from __future__ import annotations

from typing import Protocol

from src.context_builder import build_context
from src.data_validator import validate_knowledge_base
from src.intent_classifier import classify_intent
from src.models import AgentResponse, KnowledgeBase
from src.prompts import SYSTEM_PROMPT, build_user_prompt
from src.response_validator import validate_response


class LLMClientProtocol(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


def answer_user_message(
    user_message: str,
    knowledge_base: KnowledgeBase,
    llm_client: LLMClientProtocol,
) -> AgentResponse:
    cleaned_message = user_message.strip()
    if not cleaned_message:
        raise ValueError("A mensagem do usuário não pode estar vazia.")

    validation_report = validate_knowledge_base(knowledge_base, raise_on_error=True)
    intent = classify_intent(cleaned_message)
    context = build_context(intent, cleaned_message, knowledge_base, validation_report)
    user_prompt = build_user_prompt(cleaned_message, context)
    content = llm_client.generate(SYSTEM_PROMPT, user_prompt)
    warnings = validate_response(content, context)
    return AgentResponse(content=content, intent=intent, context=context, warnings=warnings)
