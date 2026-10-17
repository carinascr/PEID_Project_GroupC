from pathlib import Path
import json
import sqlite3

import assistant
from contracts import format_context, load_contracts, search_contracts
from presentation import format_answer
from vector_store import ContractVectorStore


DATASET = Path(__file__).parents[1] / "data" / "contratos_formatados.csv"


def test_loader_detects_xlsx_bytes_with_csv_extension():
    contracts = load_contracts(DATASET)
    assert len(contracts) == 145
    assert contracts[0].record_id == "contrato-0001"
    assert "Objeto do Contrato:" in contracts[0].text


def test_search_matches_exact_cpv_and_preserves_source_id():
    contracts = load_contracts(DATASET)
    results = search_contracts(contracts, "CPV 72000000-5")
    assert results
    assert results[0][0].fields["CPV"] == "72000000-5"
    assert "contrato-" in format_context(results)


def test_search_empty_query_has_no_fabricated_results():
    assert search_contracts(load_contracts(DATASET), "   ") == []


def test_vector_store_returns_matching_contract_ids():
    contracts = load_contracts(DATASET)
    store = ContractVectorStore(
        (contract.record_id, contract.text) for contract in contracts
    )
    results = store.search("requisitos da ENTI", limit=1)
    assert results
    assert results[0][0] == "contrato-0001"


def test_search_combines_vector_scores_with_lexical_scores():
    contracts = load_contracts(DATASET)
    results = search_contracts(contracts, "requisitos da ENTI")
    assert results
    assert results[0][0].record_id == "contrato-0001"


def test_search_ranks_requested_number_of_largest_contracts():
    contracts = load_contracts(DATASET)
    results = search_contracts(contracts, "Quais os 10 maiores contratos?")
    assert len(results) == 10
    prices = [float(contract.fields["Preço Contratual"]) for contract, _ in results]
    assert prices == sorted(prices, reverse=True)


def test_largest_contract_question_is_answered_without_llm_unknown():
    result = assistant.answer_question(
        load_contracts(DATASET), "Quais os 10 maiores contratos?"
    )
    assert result["confidence"] == "high"
    assert result["answer"].startswith("1) contrato-")
    assert len(result["record_ids"]) == 10


def test_ranked_answers_render_as_compact_markdown_table():
    rendered = format_answer(
        "1) contrato-0001 — 6750 — Compra de computadores portáteis\n"
        "2) contrato-0002 — 5000 — Serviços de manutenção"
    )
    assert "| # | Contract | Contract price |" in rendered
    assert "Compra de computadores portáteis" in rendered
    assert "`contrato-0001`" not in rendered


def test_ranked_answer_keeps_long_contract_summary_minimal():
    rendered = format_answer(
        "1) contrato-0001 — 6750 — "
        "Aquisição de serviços muito longos para uma descrição contratual extensa"
    )
    assert "…" in rendered


def test_answer_question_records_evaluation_trace(monkeypatch, tmp_path):
    trace_db = tmp_path / "traces.sqlite3"
    trace_csv = tmp_path / "traces.csv"
    monkeypatch.setenv("EVALUATION_TRACE_DB", str(trace_db))
    monkeypatch.setenv("EVALUATION_TRACE_CSV", str(trace_csv))

    assistant.answer_question(
        load_contracts(DATASET), "Quais os 10 maiores contratos?"
    )

    with sqlite3.connect(trace_db) as connection:
        row = connection.execute(
            """
            SELECT input_text, output_json, prompt_version, latency_ms
            FROM traces
            """
        ).fetchone()

    assert row[0] == "Quais os 10 maiores contratos?"
    assert json.loads(row[1])["confidence"] == "high"
    assert row[2] == "contract_qa_v1"
    assert row[3] >= 0

    csv_lines = trace_csv.read_text(encoding="utf-8").splitlines()
    assert csv_lines[0].startswith("trace_id,created_at,input_text,output_json,")
    assert len(csv_lines) == 2
    assert "Quais os 10 maiores contratos?" in csv_lines[1]
