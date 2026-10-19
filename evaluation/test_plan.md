# Contract QA evaluation test plan

## Objective

Measure whether the contract assistant answers the populated cases in
`goldenset.xlsx` correctly, while preserving the question, golden answer,
candidate answer, cited records, judge evidence, and verdict for every case.
The workbook is read-only source data; blank rows are excluded.

## Test cases

| Case set | Source | Check | Expected result |
|---|---|---|---|
| Golden answer | `evaluation/goldenset.xlsx` | Execute every populated question | One evidence record per populated row |
| Deterministic | Golden answer and candidate answer | Exact supported answer appears in candidate | `pass` or `fail` |
| Unsupported | Rows whose expected answer is `#VALUE!` | Do not score as correct/incorrect | `unknown` |
| LLM judge | One criterion per case | Judge agrees with the golden answer | `PASS`, `FAIL`, or `UNKNOWN` with evidence quote |
| Provenance | Candidate JSON | Record IDs remain available | IDs saved in evidence |

## Metrics

For scorable rows, `PASS` is the positive class:

- **Accuracy** = `(true positives + true negatives) / scorable cases`.
- **Precision** = `true positives / predicted positives`.
- **Recall** = `true positives / actual positives`.
- Rows with an explicit `#VALUE!` expected answer are `UNKNOWN` and excluded
  from the binary denominator. They remain visible in the evidence file.
- Judge `UNKNOWN` results are also excluded from the judge agreement accuracy
  denominator and are reported separately as `judge_unknown_cases`.

These are answer-level metrics. They do not prove retrieval recall, factual
coverage outside the golden set, or quality of prose. The LLM judge is
single-criterion and must quote candidate evidence before its verdict.

## Execution

Deterministic, offline-compatible run:

```bash
python evaluation/run_judge.py
```

LLM-as-a-judge run (requires the configured environment, without printing
credentials):

```bash
python evaluation/run_judge.py --judge
```

Each run writes `evaluation/latest_results.json`. Preserve a dated copy when
collecting submission evidence, for example:

```bash
python evaluation/run_judge.py \
  --output evaluation/results/2026-10-19-deterministic.json
```

## Execution results

Results are generated from the current checkout and recorded in
`evaluation/latest_results.json`. The report includes the mode, denominators,
all per-case inputs and outputs, deterministic status, judge verdict, evidence
quote, and reason. Do not report an LLM-judge score until the `--judge` run has
completed successfully.
