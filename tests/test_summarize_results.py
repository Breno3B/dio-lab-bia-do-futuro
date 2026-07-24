"""Testes da consolidação de relatórios de avaliação."""

from __future__ import annotations

import json

from evaluation.summarize_results import summarize_report


def test_summarize_report_identifies_critical_and_numeric_failures(tmp_path):
    path = tmp_path / "report.json"
    path.write_text(
        json.dumps(
            {
                "model": "qwen3:4b",
                "total": 2,
                "passed": 0,
                "failed": 2,
                "blocked": 1,
                "execution_mismatches": 1,
                "expected_execution_counts": {
                    "deterministic": 1,
                    "generative": 1,
                },
                "actual_execution_counts": {
                    "deterministic": 2,
                    "generative": 0,
                },
                "results": [
                    {
                        "id": "critical_001",
                        "severity": "critical",
                        "passed": False,
                        "value_matches": True,
                    },
                    {
                        "id": "numeric_001",
                        "severity": "high",
                        "passed": False,
                        "value_matches": False,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = summarize_report(path)

    assert summary["model"] == "qwen3:4b"
    assert summary["critical_failures"] == ["critical_001"]
    assert summary["numeric_failures"] == ["numeric_001"]
    assert summary["execution_mismatches"] == 1
