"""Cliente isolado para comunicação com Ollama."""

from __future__ import annotations

import logging
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

from src.config import SETTINGS, Settings
from src.exceptions import LLMUnavailableError

logger = logging.getLogger(__name__)


class OllamaLLMClient:
    """Adaptador da biblioteca oficial do Ollama com import tardio."""

    def __init__(self, settings: Settings = SETTINGS) -> None:
        self.settings = settings

    def is_available(self) -> bool:
        request = urllib.request.Request(
            f"{self.settings.ollama_host.rstrip('/')}/api/tags",
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                return response.status == 200
        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    def _client(self) -> Any:
        try:
            from ollama import Client
        except ImportError as exc:
            raise LLMUnavailableError(
                "A dependência 'ollama' não está instalada. Execute: pip install -r requirements.txt"
            ) from exc
        return Client(host=self.settings.ollama_host, timeout=self.settings.ollama_timeout_seconds)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.is_available():
            raise LLMUnavailableError(
                f"O Ollama não está disponível em {self.settings.ollama_host}. "
                "Inicie o serviço e confirme que o modelo está instalado."
            )
        try:
            response = self._client().chat(
                model=self.settings.ollama_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=False,
                think=False,
                keep_alive="10m",
                options={"temperature": self.settings.ollama_temperature},
                
            )
            content = response["message"]["content"]
            if not str(content).strip():
                raise LLMUnavailableError("O modelo retornou uma resposta vazia.")
            return str(content).strip()
        except LLMUnavailableError:
            raise
        except Exception as exc:  # biblioteca pode lançar exceções específicas por versão
            logger.exception("Falha ao consultar o Ollama")
            raise LLMUnavailableError(f"Falha ao gerar resposta com Ollama: {exc}") from exc

    def stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        if not self.is_available():
            raise LLMUnavailableError(
                f"O Ollama não está disponível em {self.settings.ollama_host}."
            )
        try:
            chunks = self._client().chat(
                model=self.settings.ollama_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                options={"temperature": self.settings.ollama_temperature},
                stream=True,
            )
            for chunk in chunks:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield str(content)
        except Exception as exc:
            logger.exception("Falha durante streaming do Ollama")
            raise LLMUnavailableError(f"Falha ao gerar resposta com Ollama: {exc}") from exc
