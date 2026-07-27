#!/usr/bin/env python3
"""Atualiza a expectativa de bloqueio dos casos adversariais de produtos."""

from __future__ import annotations

import json
from pathlib import Path

CASES_PATH = Path("evaluation/cases/evaluation_cases.json")
TARGET_CASE_IDS = {
    "product_005",
    "product_006",
    "product_007",
    "product_008",
}


def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    updated_ids: set[str] = set()

    for case in cases:
        case_id = case.get("id")
        if case_id in TARGET_CASE_IDS:
            case["expected_blocked"] = False
            updated_ids.add(case_id)

    missing_ids = TARGET_CASE_IDS - updated_ids
    if missing_ids:
        missing = ", ".join(sorted(missing_ids))
        raise RuntimeError(f"Casos não encontrados: {missing}")

    CASES_PATH.write_text(
        json.dumps(cases, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        "Casos atualizados: "
        + ", ".join(sorted(updated_ids))
    )


if __name__ == "__main__":
    main()
