"""Configurações centralizadas da aplicação."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _get_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"A variável {name} deve conter um número.") from exc


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuração imutável carregada por variáveis de ambiente."""

    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    ollama_temperature: float = _get_float_env("OLLAMA_TEMPERATURE", 0.2)
    ollama_timeout_seconds: float = _get_float_env("OLLAMA_TIMEOUT_SECONDS", 120.0)
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @property
    def transactions_file(self) -> Path:
        return self.data_dir / "transacoes.csv"

    @property
    def service_history_file(self) -> Path:
        return self.data_dir / "historico_atendimento.csv"

    @property
    def investor_profile_file(self) -> Path:
        return self.data_dir / "perfil_investidor.json"

    @property
    def financial_products_file(self) -> Path:
        return self.data_dir / "produtos_financeiros.json"


SETTINGS = Settings()
