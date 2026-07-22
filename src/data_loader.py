"""Carregamento local da base de conhecimento."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import SETTINGS, Settings
from src.exceptions import DataLoadingError
from src.models import KnowledgeBase


def _ensure_file(path: Path) -> None:
    if not path.exists():
        raise DataLoadingError(f"Arquivo não encontrado: {path}")
    if not path.is_file():
        raise DataLoadingError(f"O caminho não representa um arquivo: {path}")


def _read_csv(path: Path) -> pd.DataFrame:
    _ensure_file(path)
    try:
        return pd.read_csv(path, encoding="utf-8")
    except (OSError, UnicodeError, pd.errors.ParserError) as exc:
        raise DataLoadingError(f"Não foi possível ler o CSV {path.name}: {exc}") from exc


def _read_json(path: Path) -> Any:
    _ensure_file(path)
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DataLoadingError(f"Não foi possível ler o JSON {path.name}: {exc}") from exc


def load_transactions(settings: Settings = SETTINGS) -> pd.DataFrame:
    dataframe = _read_csv(settings.transactions_file)
    if "data" in dataframe.columns:
        dataframe["data"] = pd.to_datetime(dataframe["data"], errors="coerce")
    if "valor" in dataframe.columns:
        dataframe["valor"] = pd.to_numeric(dataframe["valor"], errors="coerce")
    return dataframe


def load_service_history(settings: Settings = SETTINGS) -> pd.DataFrame:
    dataframe = _read_csv(settings.service_history_file)
    if "data" in dataframe.columns:
        dataframe["data"] = pd.to_datetime(dataframe["data"], errors="coerce")
    if "resolvido" in dataframe.columns:
        normalized = dataframe["resolvido"].astype(str).str.strip().str.casefold()
        dataframe["resolvido"] = normalized.map({"sim": True, "não": False, "nao": False})
    return dataframe


def load_investor_profile(settings: Settings = SETTINGS) -> dict[str, Any]:
    value = _read_json(settings.investor_profile_file)
    if not isinstance(value, dict):
        raise DataLoadingError("perfil_investidor.json deve conter um objeto JSON.")
    return value


def load_financial_products(settings: Settings = SETTINGS) -> list[dict[str, Any]]:
    value = _read_json(settings.financial_products_file)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise DataLoadingError("produtos_financeiros.json deve conter uma lista de objetos.")
    return value


def load_knowledge_base(settings: Settings = SETTINGS) -> KnowledgeBase:
    """Carrega todos os arquivos sem alterar os dados persistidos."""
    return KnowledgeBase(
        transactions=load_transactions(settings),
        service_history=load_service_history(settings),
        investor_profile=load_investor_profile(settings),
        financial_products=load_financial_products(settings),
    )
