"""Respostas determinísticas para intenções simples e totalmente calculadas."""

from __future__ import annotations

from typing import Any

from src.models import AgentContext, Intent


def _currency(value: Any) -> str:
    number = float(value)
    formatted = f"{number:,.2f}"
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def _percentage(value: Any) -> str:
    return f"{float(value):.2f}%".replace(".", ",")


def build_deterministic_response(context: AgentContext) -> str | None:
    """Retorna uma resposta local quando o LLM não agrega valor relevante."""

    if context.intent is Intent.FINANCIAL_SUMMARY:
        values = context.calculated_results
        period = (context.period or {}).get("descricao", "período disponível")
        return (
            f"Resumo: entre {period}, as entradas totalizaram {_currency(values['total_entradas'])} "
            f"e as saídas {_currency(values['total_saidas'])}. "
            f"O saldo calculado foi de {_currency(values['saldo'])}, com "
            f"{values['quantidade_transacoes']} transações consideradas."
        )

    if context.intent is Intent.EXPENSE_ANALYSIS:
        values = context.calculated_results
        largest = values.get("maior_categoria")
        if not largest:
            return "Não foram encontradas despesas no período disponível."
        period = (context.period or {}).get("descricao", "período disponível")
        return (
            f"Entre {period}, a maior categoria de gastos foi "
            f"**{largest['categoria']}**, com {_currency(largest['valor'])}, "
            f"equivalente a {_percentage(largest['participacao_percentual'])} "
            f"das saídas. O total de despesas foi {_currency(values['total_saidas'])}."
        )

    if context.intent is Intent.LOWEST_EXPENSE_CATEGORY:
        values = context.calculated_results
        smallest = values.get("menor_categoria")
        if not smallest:
            return "Não foram encontradas despesas no período disponível."
        period = (context.period or {}).get("descricao", "período disponível")
        return (
            f"Entre {period}, a menor categoria de gastos foi "
            f"**{smallest['categoria']}**, com {_currency(smallest['valor'])}, "
            f"equivalente a {_percentage(smallest['participacao_percentual'])} "
            f"das saídas. O total de despesas foi {_currency(values['total_saidas'])}."
        )

    if context.intent is Intent.GOAL_PROGRESS:
        goals = context.calculated_results.get("progresso_metas", [])
        if not goals:
            return "Nenhuma meta financeira foi encontrada na base."
        goal = goals[0]
        if goal.get("valor_atual") is None:
            return str(goal.get("observacao") or "Não há dados suficientes para calcular a meta.")
        return (
            f"Na meta **{goal['meta']}**, o valor atual é {_currency(goal['valor_atual'])} "
            f"de {_currency(goal['valor_necessario'])}. O progresso calculado é "
            f"{_percentage(goal['progresso_percentual'])}, e faltam "
            f"{_currency(goal['valor_restante'])}."
        )

    if context.intent is Intent.PERIOD_COMPARISON and not context.calculated_results:
        return (
            "A base atual não contém dois períodos completos para uma comparação segura. "
            "É necessário incluir um período anterior antes de calcular a variação."
        )

    if context.intent is Intent.CURRENT_MARKET_DATA:
        return (
            "A base local não possui dados de mercado em tempo real. "
            "Por isso, não posso informar uma cotação, taxa ou preço atual."
        )

    if context.intent is Intent.OUT_OF_SCOPE:
        return "Essa solicitação está fora do escopo financeiro da ClaraMente."

    if context.intent is Intent.UNKNOWN:
        return (
            "Não identifiquei com segurança qual análise financeira você deseja. "
            "Informe se quer consultar saldo, gastos, metas, histórico ou produtos."
        )

    return None
