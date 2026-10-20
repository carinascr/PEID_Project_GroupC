"""Run the golden-set agent evaluation and save reproducible evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.judge_agent import (  # noqa: E402
    calculate_metrics,
    evidence_to_json,
    run_evaluation,
)
from src.contracts import load_contracts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Call the one-criterion LLM judge through src.llm.ask.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evaluation" / "latest_results.json",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Evaluate only the first N populated golden-set cases.",
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be greater than zero.")

    contracts = load_contracts(ROOT / "data" / "contratos_formatados.csv")
    evidence = run_evaluation(
        contracts,
        use_llm_judge=args.judge,
        limit=args.limit,
    )
    report = {
        "mode": "llm_judge" if args.judge else "deterministic",
        "golden_set": "evaluation/goldenset.xlsx",
        "metrics": calculate_metrics(evidence),
        "cases": evidence_to_json(evidence),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    metrics = report["metrics"]
    print(
        f"mode={report['mode']} cases={metrics['cases']} "
        f"scorable={metrics['scorable_cases']} "
        f"accuracy={metrics['accuracy']:.2%} "
        f"precision={metrics['precision']:.2%} "
        f"recall={metrics['recall']:.2%}"
    )
    print(f"evidence={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
