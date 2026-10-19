---
name: run-eval
description: Run the contract assistant evaluation and summarize deterministic pass rates.
---

When asked to evaluate, score, or report on the golden set:

1. Run `python evaluation/run_judge.py` for the deterministic baseline.
2. Run `python evaluation/run_judge.py --judge` when an LLM-as-a-judge score is requested.
3. Report case counts, accuracy, precision, recall, unknown count, and evidence path.
4. Report failing case IDs from the saved JSON evidence.
5. Do not expose environment variables or API keys.
