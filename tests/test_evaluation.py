from pathlib import Path

from evaluation.judge_agent import (
    GoldenCase,
    calculate_metrics,
    deterministic_status,
    run_evaluation,
    load_golden_cases,
)
from src.assistant import answer_question
from src.contracts import load_contracts


ROOT = Path(__file__).parents[1]


def test_golden_workbook_loads_only_populated_cases():
    cases = load_golden_cases(ROOT / "evaluation" / "goldenset.xlsx")

    assert len(cases) == 23
    assert cases[0].case_id == "1"
    assert cases[15].case_id == "16"
    assert "EMEL" in cases[15].expected_answer
    assert cases[-1].expected_answer == "14600"


def test_deterministic_status_preserves_unknown_expected_answers():
    assert deterministic_status("145", "The answer is 145.") == "pass"
    assert deterministic_status("145", "The answer is 34.") == "fail"
    assert deterministic_status("#VALUE!", "unknown") == "unknown"
    assert deterministic_status("€4286092,58", "€4,286,092.58") == "pass"
    assert deterministic_status("€29559,26", "€29,559.26") == "pass"


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


def test_analytics_answers_golden_aggregate_questions_without_model_fallback():
    contracts = load_contracts(ROOT / "data" / "contratos_formatados.csv")

    assert answer_question(contracts, "How many contracts are in the file?")["answer"] == "145"
    assert answer_question(contracts, "How many columns does the file have?")["answer"] == "34"
    assert answer_question(contracts, "What is the total value of all contracts (Preço Contratual)?")["answer"] == "€4,286,092.58"
    assert answer_question(contracts, "What is the highest contract price?")["answer"] == "€200,000.00 (2 contracts share this price)"
    assert answer_question(contracts, "How many contracts used that procedure type (direct award)?")["answer"] == "116"
    assert answer_question(contracts, "How many contracts are for “Aquisição de bens móveis” (goods)?")["answer"] == "30"
    assert answer_question(contracts, "Qual a soma de contratos atribuidos à FBCPS, por ajuste direto pela Carris?")["answer"] == "€95,257.83"


def test_llm_judge_failures_become_explicit_unknown_evidence():
    contracts = load_contracts(ROOT / "data" / "contratos_formatados.csv")

    def unavailable_judge(**_kwargs):
        raise TimeoutError("judge timed out")

    evidence = run_evaluation(
        contracts,
        use_llm_judge=True,
        judge=unavailable_judge,
        limit=1,
    )

    assert evidence[0].judge_verdict == "UNKNOWN"
    assert "TimeoutError" in evidence[0].judge_reason


def test_non_scorable_cases_do_not_call_llm_judge():
    contracts = load_contracts(ROOT / "data" / "contratos_formatados.csv")

    def unexpected_judge(**_kwargs):
        raise AssertionError("non-scorable case should not call the judge")

    evidence = run_evaluation(
        contracts,
        use_llm_judge=True,
        judge=unexpected_judge,
    )

    assert [item.judge_verdict for item in evidence[-2:]] == ["UNKNOWN", "UNKNOWN"]
