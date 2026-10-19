from pathlib import Path

from evaluation.judge_agent import (
    GoldenCase,
    calculate_metrics,
    deterministic_status,
    load_golden_cases,
)


ROOT = Path(__file__).parents[1]


def test_golden_workbook_loads_only_populated_cases():
    cases = load_golden_cases(ROOT / "evaluation" / "goldenset.xlsx")

    assert len(cases) == 13
    assert cases[0].case_id == "1"
    assert cases[-1].expected_answer == "#VALUE!"


def test_deterministic_status_preserves_unknown_expected_answers():
    assert deterministic_status("145", "The answer is 145.") == "pass"
    assert deterministic_status("145", "The answer is 34.") == "fail"
    assert deterministic_status("#VALUE!", "unknown") == "unknown"


def test_metrics_exclude_unknown_cases_and_report_binary_scores():
    from evaluation.judge_agent import CaseEvidence

    evidence = [
        CaseEvidence("1", "q", "expected", "answer", [], "pass", "PASS", "quote", "ok"),
        CaseEvidence("2", "q", "expected", "answer", [], "fail", "FAIL", "quote", "ok"),
        CaseEvidence("3", "q", "#VALUE!", "answer", [], "unknown", "UNKNOWN", "unknown", "n/a"),
    ]

    metrics = calculate_metrics(evidence)

    assert metrics["scorable_cases"] == 2
    assert metrics["unknown_cases"] == 1
    assert metrics["judge_unknown_cases"] == 0
    assert metrics["answer_pass_rate"] == 0.5
    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
