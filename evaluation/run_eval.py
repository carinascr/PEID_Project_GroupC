"""Run retrieval checks over the pre-labelled golden set without an API call."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from contracts import load_contracts, search_contracts


ROOT = Path(__file__).parents[1]


def main() -> int:
    contracts = load_contracts(ROOT / "data" / "contratos_formatados.csv")
    cases = list(csv.DictReader((ROOT / "evaluation" / "golden.csv").open(encoding="utf-8")))
    passed = 0
    failures = []
    for case in cases:
        results = search_contracts(contracts, case["question"])
        context = "\n".join(contract.text for contract, _ in results)
        if case["expected_terms"].casefold() in context.casefold():
            passed += 1
        else:
            failures.append(case["id"])
    print(f"retrieval_cases={len(cases)} passed={passed} pass_rate={passed / len(cases):.2%}")
    if failures:
        print("failed_cases=" + ",".join(failures))
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
