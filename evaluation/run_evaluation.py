"""Executa a suíte end-to-end de avaliação da ClaraMente."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import SETTINGS
from src.data_loader import load_knowledge_base
from src.llm_client import OllamaLLMClient
from src.orchestrator import answer_user_message

ROOT = Path(__file__).resolve().parent
DEFAULT_CASES = ROOT / "cases" / "evaluation_cases.json"
RESULTS_DIR = ROOT / "results"

VALID_EXECUTIONS = {"deterministic", "generative"}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}


def _validate_cases(cases: Any) -> list[dict[str, Any]]:
    if not isinstance(cases, list) or not cases:
        raise ValueError("O arquivo de casos deve conter uma lista não vazia.")

    required_fields = {
        "id",
        "category",
        "severity",
        "execution",
        "question",
        "expected_intent",
    }
    seen_ids: set[str] = set()
    validated: list[dict[str, Any]] = []

    for index, raw_case in enumerate(cases, start=1):
        if not isinstance(raw_case, dict):
            raise ValueError(f"O caso {index} deve ser um objeto JSON.")

        missing = sorted(required_fields - raw_case.keys())
        if missing:
            raise ValueError(
                f"O caso {index} não possui os campos obrigatórios: {missing}."
            )

        case_id = str(raw_case["id"]).strip()
        if not case_id:
            raise ValueError(f"O caso {index} possui id vazio.")
        if case_id in seen_ids:
            raise ValueError(f"ID de caso duplicado: {case_id}.")
        seen_ids.add(case_id)

        execution = str(raw_case["execution"]).strip()
        if execution not in VALID_EXECUTIONS:
            raise ValueError(
                f"Execução inválida no caso {case_id}: {execution}. "
                f"Valores permitidos: {sorted(VALID_EXECUTIONS)}."
            )

        severity = str(raw_case["severity"]).strip()
        if severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Severidade inválida no caso {case_id}: {severity}. "
                f"Valores permitidos: {sorted(VALID_SEVERITIES)}."
            )

        for field_name in ("required_terms", "forbidden_terms"):
            terms = raw_case.get(field_name, [])
            if not isinstance(terms, list) or not all(
                isinstance(term, str) and term.strip() for term in terms
            ):
                raise ValueError(
                    f"O campo {field_name} do caso {case_id} deve ser "
                    "uma lista de textos não vazios."
                )

        for field_name in ("expected_used_llm", "expected_blocked"):
            value = raw_case.get(field_name)
            if value is not None and not isinstance(value, bool):
                raise ValueError(
                    f"O campo {field_name} do caso {case_id} deve ser booleano."
                )

        validated.append(raw_case)

    return validated


def _is_blocked(response: Any) -> bool:
    return any(
        "Resposta bloqueada:" in warning
        for warning in response.warnings
    )


def _evaluate_case(case: dict[str, Any], response: Any) -> dict[str, Any]:
    normalized = response.content.casefold()
    failures: list[str] = []

    expected_intent = case["expected_intent"]
    if response.intent.value != expected_intent:
        failures.append(
            f"Intenção esperada={expected_intent}, "
            f"obtida={response.intent.value}."
        )

    for term in case.get("required_terms", []):
        if term.casefold() not in normalized:
            failures.append(f"Termo obrigatório ausente: {term}")

    for term in case.get("forbidden_terms", []):
        if term.casefold() in normalized:
            failures.append(f"Termo proibido presente: {term}")

    blocked = _is_blocked(response)
    expected_blocked = case.get("expected_blocked")
    if expected_blocked is not None and blocked != expected_blocked:
        failures.append(
            f"Bloqueio esperado={expected_blocked}, obtido={blocked}."
        )

    used_llm = bool(response.performance_metrics.get("used_llm", False))
    expected_used_llm = case.get("expected_used_llm")
    if expected_used_llm is not None and used_llm != expected_used_llm:
        failures.append(
            f"Uso do LLM esperado={expected_used_llm}, obtido={used_llm}."
        )

    return {
        "id": case["id"],
        "category": case["category"],
        "severity": case["severity"],
        "execution": case["execution"],
        "question": case["question"],
        "expected_intent": expected_intent,
        "intent": response.intent.value,
        "expected_used_llm": expected_used_llm,
        "used_llm": used_llm,
        "expected_blocked": expected_blocked,
        "blocked": blocked,
        "passed": not failures,
        "failures": failures,
        "response": response.content,
        "warnings": response.warnings,
        "performance": response.performance_metrics,
        "notes": case.get("notes"),
    }


def _group_summary(
    results: list[dict[str, Any]],
    field_name: str,
) -> dict[str, dict[str, int]]:
    grouped: dict[str, dict[str, int]] = {}
    values: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for result in results:
        values[str(result[field_name])].append(result)

    for value, items in sorted(values.items()):
        grouped[value] = {
            "total": len(items),
            "passed": sum(item["passed"] for item in items),
            "failed": sum(not item["passed"] for item in items),
            "blocked": sum(item["blocked"] for item in items),
            "used_llm": sum(item["used_llm"] for item in items),
        }

    return grouped


def _build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "executed_at": datetime.now(UTC).isoformat(),
        "model": SETTINGS.ollama_model,
        "total": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": sum(not item["passed"] for item in results),
        "blocked": sum(item["blocked"] for item in results),
        "deterministic": sum(not item["used_llm"] for item in results),
        "generative": sum(item["used_llm"] for item in results),
        "by_category": _group_summary(results, "category"),
        "by_severity": _group_summary(results, "severity"),
        "by_execution": _group_summary(results, "execution"),
        "failure_reasons": dict(
            Counter(
                failure
                for item in results
                for failure in item["failures"]
            )
        ),
        "results": results,
    }


def run(
    cases_file: Path,
    output_file: Path | None = None,
    *,
    category: str | None = None,
    execution: str | None = None,
) -> Path:
    raw_cases = json.loads(cases_file.read_text(encoding="utf-8"))
    cases = _validate_cases(raw_cases)

    if category:
        cases = [case for case in cases if case["category"] == category]
    if execution:
        cases = [case for case in cases if case["execution"] == execution]

    if not cases:
        raise ValueError("Nenhum caso corresponde aos filtros informados.")

    knowledge_base = load_knowledge_base()
    client = OllamaLLMClient()
    results: list[dict[str, Any]] = []

    for position, case in enumerate(cases, start=1):
        print(f"[{position}/{len(cases)}] {case['id']}")
        response = answer_user_message(
            case["question"],
            knowledge_base,
            client,
        )
        results.append(_evaluate_case(case, response))

    summary = _build_summary(results)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    destination = output_file or RESULTS_DIR / (
        datetime.now(UTC).strftime("evaluation_%Y%m%d_%H%M%S.json")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executa a suíte end-to-end de avaliação da ClaraMente."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--category",
        help="Executa somente uma categoria presente no arquivo de casos.",
    )
    parser.add_argument(
        "--execution",
        choices=sorted(VALID_EXECUTIONS),
        help="Executa somente casos determinísticos ou generativos.",
    )
    args = parser.parse_args()

    output = run(
        args.cases,
        args.output,
        category=args.category,
        execution=args.execution,
    )
    print(f"Relatório salvo em: {output}")


if __name__ == "__main__":
    main()
