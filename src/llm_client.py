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
        self.last_metrics: dict[str, Any] = {}

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
                "A dependência 'ollama' não está instalada. "
                "Execute: pip install -r requirements.txt"
            ) from exc
        return Client(
            host=self.settings.ollama_host,
            timeout=self.settings.ollama_timeout_seconds,
        )

    @staticmethod
    def _duration_ms(value: Any) -> float | None:
        if not isinstance(value, (int, float)):
            return None
        return round(float(value) / 1_000_000, 2)

    def _capture_metrics(self, response: Any) -> None:
        prompt_count = response.get("prompt_eval_count")
        eval_count = response.get("eval_count")
        eval_duration = response.get("eval_duration")
        tokens_per_second = None
        if isinstance(eval_count, int) and isinstance(eval_duration, (int, float)) and eval_duration > 0:
            tokens_per_second = round(eval_count / (eval_duration / 1_000_000_000), 2)

        self.last_metrics = {
            "prompt_eval_count": prompt_count if isinstance(prompt_count, int) else None,
            "eval_count": eval_count if isinstance(eval_count, int) else None,
            "prompt_eval_duration_ms": self._duration_ms(response.get("prompt_eval_duration")),
            "eval_duration_ms": self._duration_ms(eval_duration),
            "load_duration_ms": self._duration_ms(response.get("load_duration")),
            "tokens_per_second": tokens_per_second,
        }

    def _chat_options(self) -> dict[str, Any]:
        return {
            "temperature": self.settings.ollama_temperature,
            "num_ctx": self.settings.ollama_num_ctx,
            "num_predict": self.settings.ollama_num_predict,
        }

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.is_available():
            raise LLMUnavailableError(
                "O modelo local não está disponível. "
                "Confirme se o serviço está em execução."
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
                options={
                    "temperature": self.settings.ollama_temperature,
                    "num_ctx": self.settings.ollama_num_ctx,
                    "num_predict": self.settings.ollama_num_predict,
                },
            )
            self._capture_metrics(response)
            content = response["message"]["content"]
            if not str(content).strip():
                raise LLMUnavailableError("O modelo retornou uma resposta vazia.")
            return str(content).strip()
        except LLMUnavailableError:
            raise
        except Exception as exc:
            logger.exception("Falha ao consultar o Ollama")
            raise LLMUnavailableError(
                "Não foi possível consultar o modelo local."
            ) from exc

    def stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        if not self.is_available():
            raise LLMUnavailableError(
                "O modelo local não está disponível. "
                "Confirme se o serviço está em execução."
            )
        try:
            chunks = self._client().chat(
                model=self.settings.ollama_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
                think=False,
                keep_alive="10m",
                options={
                    "temperature": self.settings.ollama_temperature,
                    "num_ctx": self.settings.ollama_num_ctx,
                    "num_predict": self.settings.ollama_num_predict,
                },
            )
            final_chunk: Any = None
            for chunk in chunks:
                final_chunk = chunk
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield str(content)
            if final_chunk is not None:
                self._capture_metrics(final_chunk)
        except Exception as exc:
            logger.exception("Falha durante streaming do Ollama")
            raise LLMUnavailableError(
                "Não foi possível consultar o modelo local."
            ) from exc
