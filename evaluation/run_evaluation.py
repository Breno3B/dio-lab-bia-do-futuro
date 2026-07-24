"""Executa a suíte end-to-end de avaliação da ClaraMente."""

from __future__ import annotations

import argparse
import json
import math
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
        "expected_used_llm",
    }
    seen_ids: set[str] = set()
    validated: list[dict[str, Any]] = []

    for index, raw_case in enumerate(cases, start=1):
        if not isinstance(raw_case, dict):
            raise TypeError(f"O caso {index} deve ser um objeto JSON.")

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

        expected_values = raw_case.get("expected_values", {})
        if not isinstance(expected_values, dict):
            raise ValueError(
                f"O campo expected_values do caso {case_id} deve ser um objeto."
            )
        if not all(
            isinstance(path, str)
            and path.strip()
            and isinstance(value, int | float)
            and not isinstance(value, bool)
            for path, value in expected_values.items()
        ):
            raise ValueError(
                f"O campo expected_values do caso {case_id} deve mapear "
                "caminhos não vazios para valores numéricos."
            )

        tolerance = raw_case.get("expected_value_tolerance", 0.01)
        if (
            not isinstance(tolerance, int | float)
            or isinstance(tolerance, bool)
            or tolerance < 0
        ):
            raise ValueError(
                f"O campo expected_value_tolerance do caso {case_id} "
                "deve ser numérico e maior ou igual a zero."
            )

        for field_name in ("expected_used_llm", "expected_blocked"):
            value = raw_case.get(field_name)
            if value is not None and not isinstance(value, bool):
                raise ValueError(
                    f"O campo {field_name} do caso {case_id} deve ser booleano."
                )

        expected_used_llm = raw_case["expected_used_llm"]
        expected_from_execution = execution == "generative"
        if expected_used_llm != expected_from_execution:
            raise ValueError(
                f"Configuração incoerente no caso {case_id}: "
                f"execution={execution} exige "
                f"expected_used_llm={expected_from_execution}."
            )

        validated.append(raw_case)

    return validated


def _is_blocked(response: Any) -> bool:
    return any(
        "Resposta bloqueada:" in warning
        for warning in response.warnings
    )


def _get_nested_value(data: Any, path: str) -> Any:
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                raise KeyError(path)
            current = current[part]
        elif isinstance(current, list):
            try:
                index = int(part)
            except ValueError as exc:
                raise KeyError(path) from exc
            if index < 0 or index >= len(current):
                raise KeyError(path)
            current = current[index]
        else:
            raise KeyError(path)
    return current


def _evaluate_expected_values(
    case: dict[str, Any],
    response: Any,
) -> tuple[dict[str, Any], list[str]]:
    expected_values = case.get("expected_values", {})
    tolerance = float(case.get("expected_value_tolerance", 0.01))
    actual_values: dict[str, Any] = {}
    failures: list[str] = []

    for path, expected in expected_values.items():
        try:
            actual = _get_nested_value(
                response.context.calculated_results,
                path,
            )
        except KeyError:
            actual_values[path] = None
            failures.append(
                f"Valor esperado não encontrado no contexto: {path}."
            )
            continue

        actual_values[path] = actual
        if (
            not isinstance(actual, int | float)
            or isinstance(actual, bool)
        ):
            failures.append(
                f"Valor obtido em {path} não é numérico: {actual!r}."
            )
            continue

        if not math.isclose(
            float(actual),
            float(expected),
            rel_tol=0.0,
            abs_tol=tolerance,
        ):
            failures.append(
                f"Valor esperado em {path}={expected}, obtido={actual}, "
                f"tolerância={tolerance}."
            )

    return actual_values, failures


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
    expected_used_llm = case["expected_used_llm"]
    actual_execution = "generative" if used_llm else "deterministic"
    execution_matches = case["execution"] == actual_execution
    if not execution_matches:
        failures.append(
            f"Execução esperada={case['execution']}, "
            f"obtida={actual_execution}."
        )

    actual_values, value_failures = _evaluate_expected_values(
        case,
        response,
    )
    failures.extend(value_failures)

    return {
        "id": case["id"],
        "category": case["category"],
        "severity": case["severity"],
        "expected_execution": case["execution"],
        "actual_execution": actual_execution,
        "execution_matches": execution_matches,
        "question": case["question"],
        "expected_intent": expected_intent,
        "intent": response.intent.value,
        "expected_used_llm": expected_used_llm,
        "used_llm": used_llm,
        "expected_blocked": expected_blocked,
        "blocked": blocked,
        "expected_values": case.get("expected_values", {}),
        "actual_values": actual_values,
        "value_matches": not value_failures,
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
        "expected_execution_counts": {
            "deterministic": sum(
                item["expected_execution"] == "deterministic"
                for item in results
            ),
            "generative": sum(
                item["expected_execution"] == "generative"
                for item in results
            ),
        },
        "actual_execution_counts": {
            "deterministic": sum(
                item["actual_execution"] == "deterministic"
                for item in results
            ),
            "generative": sum(
                item["actual_execution"] == "generative"
                for item in results
            ),
        },
        "execution_mismatches": sum(
            not item["execution_matches"] for item in results
        ),
        "by_category": _group_summary(results, "category"),
        "by_severity": _group_summary(results, "severity"),
        "by_expected_execution": _group_summary(
            results,
            "expected_execution",
        ),
        "by_actual_execution": _group_summary(
            results,
            "actual_execution",
        ),
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
