"""Executa casos adversariais end-to-end contra o Ollama real."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import SETTINGS
from src.data_loader import load_knowledge_base
from src.llm_client import OllamaLLMClient
from src.orchestrator import answer_user_message

ROOT = Path(__file__).resolve().parent
DEFAULT_CASES = ROOT / "adversarial_cases.json"
RESULTS_DIR = ROOT / "results"


def _evaluate_case(case: dict[str, Any], response: Any) -> dict[str, Any]:
    normalized = response.content.casefold()
    failures: list[str] = []

    expected_intent = case.get("expected_intent")
    if expected_intent and response.intent.value != expected_intent:
        failures.append(
            f"Intenção esperada={expected_intent}, obtida={response.intent.value}."
        )

    for term in case.get("required_terms", []):
        if str(term).casefold() not in normalized:
            failures.append(f"Termo obrigatório ausente: {term}")

    for term in case.get("forbidden_terms", []):
        if str(term).casefold() in normalized:
            failures.append(f"Termo proibido presente: {term}")

    if any("Resposta bloqueada:" in warning for warning in response.warnings):
        blocked = True
    else:
        blocked = False

    return {
        "id": case["id"],
        "question": case["question"],
        "intent": response.intent.value,
        "passed": not failures,
        "blocked": blocked,
        "failures": failures,
        "response": response.content,
        "warnings": response.warnings,
        "performance": response.performance_metrics,
    }


def run(cases_file: Path, output_file: Path | None = None) -> Path:
    cases = json.loads(cases_file.read_text(encoding="utf-8"))
    knowledge_base = load_knowledge_base()
    client = OllamaLLMClient()

    results = []
    for case in cases:
        response = answer_user_message(
            case["question"],
            knowledge_base,
            client,
        )
        results.append(_evaluate_case(case, response))

    summary = {
        "executed_at": datetime.now(UTC).isoformat(),
        "model": SETTINGS.ollama_model,
        "total": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": sum(not item["passed"] for item in results),
        "results": results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    destination = output_file or RESULTS_DIR / (
        datetime.now(UTC).strftime("adversarial_%Y%m%d_%H%M%S.json")
    )
    destination.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = run(args.cases, args.output)
    print(f"Relatório salvo em: {output}")


if __name__ == "__main__":
    main()
