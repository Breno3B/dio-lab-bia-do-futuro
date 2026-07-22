"""Seleção das fontes e construção do contexto dinâmico."""

from __future__ import annotations

from src.analytics import (
    available_period,
    calculate_expenses_by_category,
    calculate_goal_progress,
    calculate_period_summary,
    find_compatible_products,
    search_service_history,
)
from src.models import AgentContext, Intent, KnowledgeBase, ValidationReport

COMMON_LIMITATIONS = [
    "A base contém dados mockados e possui finalidade educacional.",
    "A aplicação não possui dados financeiros ou de mercado em tempo real.",
]


def build_context(
    intent: Intent,
    user_message: str,
    knowledge_base: KnowledgeBase,
    validation_report: ValidationReport | None = None,
) -> AgentContext:
    context = AgentContext(intent=intent, user_message=user_message, limitations=list(COMMON_LIMITATIONS))
    if validation_report:
        context.inconsistencies.extend(validation_report.warnings)

    transactions = knowledge_base.transactions
    profile = knowledge_base.investor_profile

    if intent is Intent.FINANCIAL_SUMMARY:
        context.sources = ["data/transacoes.csv"]
        context.period = available_period(transactions)
        context.calculated_results = calculate_period_summary(transactions)

    elif intent is Intent.EXPENSE_ANALYSIS:
        context.sources = ["data/transacoes.csv"]
        context.period = available_period(transactions)
        context.filters = {"tipo": "saida"}
        context.calculated_results = calculate_expenses_by_category(transactions)
        context.missing_data.append("Não existe orçamento mensal definido por categoria.")

    elif intent is Intent.PERIOD_COMPARISON:
        context.sources = ["data/transacoes.csv"]
        context.period = available_period(transactions)
        context.missing_data.append(
            "A base atual contém apenas um período curto; não há dois meses completos para comparação segura."
        )
        context.specific_restrictions.append("Não inventar um período anterior ausente.")

    elif intent is Intent.GOAL_PROGRESS:
        context.sources = ["data/perfil_investidor.json"]
        context.relevant_profile = {
            "objetivo_principal": profile.get("objetivo_principal"),
            "reserva_emergencia_atual": profile.get("reserva_emergencia_atual"),
            "metas": profile.get("metas", []),
        }
        context.calculated_results = {"progresso_metas": calculate_goal_progress(profile)}

    elif intent is Intent.PRODUCT_COMPATIBILITY:
        context.sources = ["data/perfil_investidor.json", "data/produtos_financeiros.json"]
        context.relevant_profile = {
            "perfil_investidor": profile.get("perfil_investidor"),
            "aceita_risco": profile.get("aceita_risco"),
            "objetivo_principal": profile.get("objetivo_principal"),
        }
        context.products = find_compatible_products(profile, knowledge_base.financial_products)
        if any("divergência" in warning.casefold() for warning in context.inconsistencies):
            context.specific_restrictions.append(
                "Não concluir compatibilidade definitiva até confirmar a divergência do perfil."
            )
        context.specific_restrictions.extend([
            "Citar somente produtos presentes no catálogo fornecido.",
            "Não tratar rentabilidade como garantia de retorno.",
        ])

    elif intent is Intent.SERVICE_HISTORY:
        context.sources = ["data/historico_atendimento.csv"]
        context.relevant_history = search_service_history(knowledge_base.service_history, user_message)
        if not context.relevant_history:
            context.missing_data.append("Nenhum atendimento relacionado foi encontrado.")
        context.specific_restrictions.append(
            "O histórico comprova apenas que o tema foi discutido, não comprova movimentações financeiras."
        )

    elif intent is Intent.CURRENT_MARKET_DATA:
        context.missing_data.append("A base local não possui dados atuais de mercado.")
        context.specific_restrictions.append("Não informar valores atuais usando conhecimento interno do modelo.")

    elif intent is Intent.OUT_OF_SCOPE:
        context.specific_restrictions.append("Responder brevemente que a solicitação está fora do escopo financeiro.")

    else:
        context.sources = [
            "data/transacoes.csv",
            "data/perfil_investidor.json",
        ]
        context.period = available_period(transactions)
        context.calculated_results = calculate_period_summary(transactions)
        context.relevant_profile = {
            "objetivo_principal": profile.get("objetivo_principal"),
        }
        context.missing_data.append("A intenção não foi identificada com confiança.")
        context.specific_restrictions.append("Pedir esclarecimento caso a pergunta permaneça ambígua.")

    return context
