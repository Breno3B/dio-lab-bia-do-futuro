"""Configurações centralizadas da aplicação."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# O arquivo é carregado uma única vez. Os testes instanciam Settings diretamente,
# depois de isolar as variáveis com monkeypatch, sem recarregar este módulo.
load_dotenv(dotenv_path=ENV_FILE, override=False)


def _get_float_env(name: str, default: float) -> float:
    """Obtém uma variável numérica do ambiente."""
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"A variável de ambiente {name} deve conter um número válido."
        ) from exc



def _get_int_env(name: str, default: int) -> int:
    """Obtém uma variável inteira positiva do ambiente."""
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"A variável de ambiente {name} deve conter um número inteiro válido."
        ) from exc

    if value <= 0:
        raise ValueError(f"A variável de ambiente {name} deve ser maior que zero.")
    return value


def _get_str_env(name: str, default: str) -> str:
    """Obtém uma variável textual, ignorando valores vazios."""
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return raw_value.strip()


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuração imutável carregada no momento da instanciação."""

    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    ollama_host: str = field(
        default_factory=lambda: _get_str_env(
            "OLLAMA_HOST",
            "http://localhost:11434",
        )
    )
    ollama_model: str = field(
        default_factory=lambda: _get_str_env("OLLAMA_MODEL", "qwen3:8b")
    )
    ollama_temperature: float = field(
        default_factory=lambda: _get_float_env("OLLAMA_TEMPERATURE", 0.2)
    )
    ollama_timeout_seconds: float = field(
        default_factory=lambda: _get_float_env(
            "OLLAMA_TIMEOUT_SECONDS",
            120.0,
        )
    )
    ollama_num_ctx: int = field(
        default_factory=lambda: _get_int_env("OLLAMA_NUM_CTX", 4096)
    )
    ollama_num_predict: int = field(
        default_factory=lambda: _get_int_env("OLLAMA_NUM_PREDICT", 250)
    )
    max_user_message_chars: int = field(
        default_factory=lambda: _get_int_env("MAX_USER_MESSAGE_CHARS", 2000)
    )
    log_level: str = field(
        default_factory=lambda: _get_str_env("LOG_LEVEL", "INFO").upper()
    )

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
