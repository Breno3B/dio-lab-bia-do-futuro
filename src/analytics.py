"""Cálculos determinísticos da ClaraMente."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd


def _as_timestamp(value: date | datetime | str | pd.Timestamp | None) -> pd.Timestamp | None:
    if value is None:
        return None
    return pd.Timestamp(value)


def filter_transactions(
    transactions: pd.DataFrame,
    start_date: date | datetime | str | pd.Timestamp | None = None,
    end_date: date | datetime | str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    filtered = transactions.copy()
    start = _as_timestamp(start_date)
    end = _as_timestamp(end_date)
    if start is not None:
        filtered = filtered[filtered["data"] >= start]
    if end is not None:
        filtered = filtered[filtered["data"] <= end]
    return filtered


def _format_date_br(value: date | datetime | pd.Timestamp) -> str:
    """Formata uma data no padrão brasileiro ``DD/MM/AAAA``."""
    return pd.Timestamp(value).strftime("%d/%m/%Y")


def available_period(transactions: pd.DataFrame) -> dict[str, str] | None:
    """Retorna o período disponível já formatado para apresentação."""
    valid_dates = transactions["data"].dropna()
    if valid_dates.empty:
        return None

    start = valid_dates.min()
    end = valid_dates.max()
    start_formatted = _format_date_br(start)
    end_formatted = _format_date_br(end)

    return {
        "inicio": start_formatted,
        "fim": end_formatted,
        "descricao": f"{start_formatted} a {end_formatted}",
    }


def calculate_period_summary(
    transactions: pd.DataFrame,
    start_date: date | datetime | str | pd.Timestamp | None = None,
    end_date: date | datetime | str | pd.Timestamp | None = None,
) -> dict[str, Any]:
    filtered = filter_transactions(transactions, start_date, end_date)
    entries = filtered.loc[filtered["tipo"].eq("entrada"), "valor"].sum()
    expenses = filtered.loc[filtered["tipo"].eq("saida"), "valor"].sum()
    return {
        "quantidade_transacoes": len(filtered),
        "total_entradas": round(float(entries), 2),
        "total_saidas": round(float(expenses), 2),
        "saldo": round(float(entries - expenses), 2),
    }


def calculate_expenses_by_category(
    transactions: pd.DataFrame,
    start_date: date | datetime | str | pd.Timestamp | None = None,
    end_date: date | datetime | str | pd.Timestamp | None = None,
) -> dict[str, Any]:
    filtered = filter_transactions(transactions, start_date, end_date)
    expenses = filtered[filtered["tipo"].eq("saida")].copy()
    total = float(expenses["valor"].sum())
    grouped = (
        expenses.groupby("categoria", as_index=False)["valor"]
        .sum()
        .sort_values("valor", ascending=False)
    )
    categories = []
    for record in grouped.to_dict(orient="records"):
        value = float(record["valor"])
        categories.append({
            "categoria": str(record["categoria"]),
            "valor": round(value, 2),
            "participacao_percentual": round((value / total * 100), 2) if total else 0.0,
        })
    return {
        "total_saidas": round(total, 2),
        "categorias": categories,
        "maior_categoria": categories[0] if categories else None,
        "menor_categoria": categories[-1] if categories else None,
    }


def compare_periods(
    transactions: pd.DataFrame,
    current_start: date | datetime | str | pd.Timestamp,
    current_end: date | datetime | str | pd.Timestamp,
    previous_start: date | datetime | str | pd.Timestamp,
    previous_end: date | datetime | str | pd.Timestamp,
) -> dict[str, Any]:
    current = calculate_period_summary(transactions, current_start, current_end)
    previous = calculate_period_summary(transactions, previous_start, previous_end)
    difference = current["total_saidas"] - previous["total_saidas"]
    previous_total = previous["total_saidas"]
    percentage = None if previous_total == 0 else round(difference / previous_total * 100, 2)
    return {
        "periodo_atual": current,
        "periodo_anterior": previous,
        "diferenca_absoluta_saidas": round(difference, 2),
        "variacao_percentual_saidas": percentage,
    }


def calculate_goal_progress(profile: dict[str, Any]) -> list[dict[str, Any]]:
    raw_current_reserve = profile.get("reserva_emergencia_atual")
    current_reserve = (
        float(raw_current_reserve) if raw_current_reserve is not None else None
    )

    results: list[dict[str, Any]] = []
    for goal in profile.get("metas", []):
        needed = float(goal["valor_necessario"])
        is_reserve = "reserva" in str(goal["meta"]).casefold()
        current = current_reserve if is_reserve else None

        if current is None:
            observation = (
                "O valor atual da reserva de emergência não foi informado."
                if is_reserve
                else "A base não informa o valor atual desta meta."
            )
            remaining = None
            progress = None
        else:
            observation = None
            remaining = round(max(needed - current, 0.0), 2)
            progress = (
                round(min(current / needed * 100, 100.0), 2)
                if needed
                else None
            )

        results.append(
            {
                "meta": goal["meta"],
                "prazo": goal["prazo"],
                "valor_atual": round(current, 2) if current is not None else None,
                "valor_necessario": round(needed, 2),
                "valor_restante": remaining,
                "progresso_percentual": progress,
                "observacao": observation,
            }
        )

    return results

def find_compatible_products(
    profile: dict[str, Any],
    products: list[dict[str, Any]],
    available_amount: float | None = None,
) -> list[dict[str, Any]]:
    accepts_risk = profile.get("aceita_risco")
    objective = str(profile.get("objetivo_principal", "")).casefold()
    allowed_risks = {"baixo"} if accepts_risk is False else {"baixo", "medio", "médio"}

    compatible: list[dict[str, Any]] = []
    for product in products:
        risk = str(product.get("risco", "")).casefold()
        minimum = float(product.get("aporte_minimo", 0.0))
        if risk not in allowed_risks:
            continue
        if available_amount is not None and minimum > available_amount:
            continue

        purpose = str(product.get("indicado_para", "")).casefold()
        objective_match = (
            ("reserva" in objective and "reserva" in purpose)
            or ("emergência" in objective and "emergência" in purpose)
            or ("emergencia" in objective and "emergencia" in purpose)
        )
        compatible.append({
            **product,
            "criterios_compatibilidade": [
                f"risco '{product['risco']}' compatível com aceita_risco={accepts_risk}",
                *( ["finalidade alinhada ao objetivo principal"] if objective_match else [] ),
                *( [f"aporte mínimo dentro do valor disponível de R$ {available_amount:.2f}"] if available_amount is not None else [] ),
            ],
            "alinhamento_objetivo": objective_match,
        })

    return sorted(compatible, key=lambda item: (not item["alinhamento_objetivo"], item["aporte_minimo"]))


def search_service_history(history: pd.DataFrame, query: str) -> list[dict[str, Any]]:
    terms = [term for term in query.casefold().split() if len(term) >= 4]
    if not terms:
        return []
    searchable = (history["tema"].fillna("") + " " + history["resumo"].fillna("")).str.casefold()
    mask = pd.Series(False, index=history.index)
    for term in terms:
        mask = mask | searchable.str.contains(term, regex=False)
    result = history[mask].sort_values("data", ascending=False).copy()
    result["data"] = result["data"].dt.strftime("%Y-%m-%d")
    return result.to_dict(orient="records")
