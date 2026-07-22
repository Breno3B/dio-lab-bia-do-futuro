"""Validações estruturais e semânticas da base de conhecimento."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd

from src.exceptions import DataValidationError
from src.models import KnowledgeBase, ValidationReport

TRANSACTION_COLUMNS = {"data", "descricao", "categoria", "valor", "tipo"}
HISTORY_COLUMNS = {"data", "canal", "tema", "resumo", "resolvido"}
PROFILE_FIELDS = {
    "nome", "idade", "profissao", "renda_mensal", "perfil_investidor",
    "objetivo_principal", "patrimonio_total", "reserva_emergencia_atual",
    "aceita_risco", "metas",
}
PRODUCT_FIELDS = {"nome", "categoria", "risco", "rentabilidade", "aporte_minimo", "indicado_para"}
ALLOWED_TRANSACTION_TYPES = {"entrada", "saida"}
ALLOWED_RISKS = {"baixo", "medio", "médio", "alto"}


def _missing_fields(actual: Iterable[str], required: set[str]) -> set[str]:
    return required - set(actual)


def validate_transactions(dataframe: pd.DataFrame) -> ValidationReport:
    report = ValidationReport()
    missing = _missing_fields(dataframe.columns, TRANSACTION_COLUMNS)
    if missing:
        report.errors.append(f"transacoes.csv sem colunas obrigatórias: {sorted(missing)}")
        return report

    if dataframe.empty:
        report.errors.append("transacoes.csv não possui registros.")
        return report

    if dataframe["data"].isna().any():
        report.errors.append("transacoes.csv possui datas inválidas ou ausentes.")
    if dataframe["valor"].isna().any():
        report.errors.append("transacoes.csv possui valores não numéricos ou ausentes.")
    if (dataframe["valor"].dropna() < 0).any():
        report.errors.append("transacoes.csv possui valores negativos; o tipo deve indicar entrada ou saída.")

    normalized_types = dataframe["tipo"].astype(str).str.strip().str.casefold()
    unknown_types = sorted(set(normalized_types) - ALLOWED_TRANSACTION_TYPES)
    if unknown_types:
        report.errors.append(f"Tipos de transação desconhecidos: {unknown_types}")

    if dataframe[["data", "descricao", "valor", "tipo"]].duplicated().any():
        report.warnings.append("Há possíveis transações duplicadas.")
    if dataframe["descricao"].astype(str).str.strip().eq("").any():
        report.errors.append("Há transações sem descrição.")
    if dataframe["categoria"].astype(str).str.strip().eq("").any():
        report.errors.append("Há transações sem categoria.")
    return report


def validate_service_history(dataframe: pd.DataFrame) -> ValidationReport:
    report = ValidationReport()
    missing = _missing_fields(dataframe.columns, HISTORY_COLUMNS)
    if missing:
        report.errors.append(f"historico_atendimento.csv sem colunas obrigatórias: {sorted(missing)}")
        return report
    if dataframe["data"].isna().any():
        report.errors.append("historico_atendimento.csv possui datas inválidas ou ausentes.")
    for column in ("canal", "tema", "resumo"):
        if dataframe[column].astype(str).str.strip().eq("").any():
            report.errors.append(f"historico_atendimento.csv possui valores vazios em {column}.")
    if dataframe["resolvido"].isna().any():
        report.warnings.append("Há atendimentos com status de resolução inválido ou ausente.")
    return report


def validate_investor_profile(profile: dict[str, Any]) -> ValidationReport:
    report = ValidationReport()
    missing = _missing_fields(profile, PROFILE_FIELDS)
    if missing:
        report.errors.append(f"perfil_investidor.json sem campos obrigatórios: {sorted(missing)}")
        return report

    numeric_fields = ("idade", "renda_mensal", "patrimonio_total", "reserva_emergencia_atual")
    for field_name in numeric_fields:
        if not isinstance(profile.get(field_name), (int, float)) or isinstance(profile.get(field_name), bool):
            report.errors.append(f"O campo {field_name} deve ser numérico.")
    if not isinstance(profile.get("aceita_risco"), bool):
        report.errors.append("O campo aceita_risco deve ser booleano.")

    metas = profile.get("metas")
    if not isinstance(metas, list):
        report.errors.append("O campo metas deve ser uma lista.")
    else:
        for index, meta in enumerate(metas):
            if not isinstance(meta, dict):
                report.errors.append(f"A meta {index} deve ser um objeto.")
                continue
            missing_meta = _missing_fields(meta, {"meta", "valor_necessario", "prazo"})
            if missing_meta:
                report.errors.append(f"A meta {index} não possui: {sorted(missing_meta)}")

    declared_profile = str(profile.get("perfil_investidor", "")).casefold()
    if declared_profile == "moderado" and profile.get("aceita_risco") is False:
        report.warnings.append(
            "Há divergência entre perfil_investidor='moderado' e aceita_risco=false."
        )
    return report


def validate_financial_products(products: list[dict[str, Any]]) -> ValidationReport:
    report = ValidationReport()
    if not products:
        report.errors.append("produtos_financeiros.json não possui produtos.")
        return report
    names: list[str] = []
    for index, product in enumerate(products):
        missing = _missing_fields(product, PRODUCT_FIELDS)
        if missing:
            report.errors.append(f"Produto {index} sem campos obrigatórios: {sorted(missing)}")
            continue
        names.append(str(product["nome"]).strip().casefold())
        if str(product["risco"]).strip().casefold() not in ALLOWED_RISKS:
            report.warnings.append(f"Produto {product['nome']} possui risco não padronizado.")
        aporte = product.get("aporte_minimo")
        if not isinstance(aporte, (int, float)) or isinstance(aporte, bool) or aporte < 0:
            report.errors.append(f"Produto {product['nome']} possui aporte_minimo inválido.")
    if len(names) != len(set(names)):
        report.warnings.append("Há produtos com nomes duplicados no catálogo.")
    return report


def validate_knowledge_base(knowledge_base: KnowledgeBase, *, raise_on_error: bool = True) -> ValidationReport:
    report = ValidationReport()
    report.extend(validate_transactions(knowledge_base.transactions))
    report.extend(validate_service_history(knowledge_base.service_history))
    report.extend(validate_investor_profile(knowledge_base.investor_profile))
    report.extend(validate_financial_products(knowledge_base.financial_products))

    if raise_on_error and report.errors:
        details = "\n".join(f"- {error}" for error in report.errors)
        raise DataValidationError(f"A base de conhecimento é inválida:\n{details}")
    return report
