"""Consolida relatórios já gerados pela suíte de avaliação."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def summarize_report(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    return {
        "file": str(path),
        "model": report.get("model"),
        "total": report.get("total", 0),
        "passed": report.get("passed", 0),
        "failed": report.get("failed", 0),
        "blocked": report.get("blocked", 0),
        "execution_mismatches": report.get("execution_mismatches", 0),
        "expected_execution_counts": report.get(
            "expected_execution_counts",
            {},
        ),
        "actual_execution_counts": report.get(
            "actual_execution_counts",
            {},
        ),
        "critical_failures": [
            result["id"]
            for result in report.get("results", [])
            if not result.get("passed", False)
            and result.get("severity") == "critical"
        ],
        "numeric_failures": [
            result["id"]
            for result in report.get("results", [])
            if not result.get("value_matches", True)
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resume relatórios JSON da avaliação."
    )
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()

    summaries = [
        summarize_report(path)
        for path in args.reports
    ]
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
