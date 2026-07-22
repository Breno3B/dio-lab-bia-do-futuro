"""Configurações centralizadas da aplicação."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Carrega configurações locais sem sobrescrever variáveis já definidas
# explicitamente no ambiente do sistema.
load_dotenv(dotenv_path=ENV_FILE, override=False)


def _get_float_env(name: str, default: float) -> float:
    """Obtém uma variável numérica do ambiente.

    Args:
        name: Nome da variável de ambiente.
        default: Valor utilizado quando a variável não foi definida.

    Returns:
        Valor convertido para ``float``.

    Raises:
        ValueError: Quando a variável existe, mas não contém um número válido.
    """
    raw_value = os.getenv(name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"A variável de ambiente {name} deve conter um número válido."
        ) from exc


def _get_str_env(name: str, default: str) -> str:
    """Obtém uma variável textual, ignorando valores vazios."""
    raw_value = os.getenv(name)

    if raw_value is None or not raw_value.strip():
        return default

    return raw_value.strip()


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuração imutável carregada a partir do ambiente."""

    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"

    ollama_host: str = _get_str_env(
        "OLLAMA_HOST",
        "http://localhost:11434",
    )
    ollama_model: str = _get_str_env(
        "OLLAMA_MODEL",
        "qwen3:8b",
    )
    ollama_temperature: float = _get_float_env(
        "OLLAMA_TEMPERATURE",
        0.2,
    )
    ollama_timeout_seconds: float = _get_float_env(
        "OLLAMA_TIMEOUT_SECONDS",
        120.0,
    )
    log_level: str = _get_str_env(
        "LOG_LEVEL",
        "INFO",
    ).upper()

    @property
    def transactions_file(self) -> Path:
        """Caminho do arquivo de transações."""
        return self.data_dir / "transacoes.csv"

    @property
    def service_history_file(self) -> Path:
        """Caminho do histórico de atendimento."""
        return self.data_dir / "historico_atendimento.csv"

    @property
    def investor_profile_file(self) -> Path:
        """Caminho do perfil do investidor."""
        return self.data_dir / "perfil_investidor.json"

    @property
    def financial_products_file(self) -> Path:
        """Caminho do catálogo de produtos financeiros."""
        return self.data_dir / "produtos_financeiros.json"


SETTINGS = Settings()
