from pathlib import Path
import json
import sqlite3

import assistant
from contracts import format_context, load_contracts, search_contracts
from presentation import format_answer
from vector_store import ContractVectorStore
from rag_database import ContractRagDatabase, build_rag_database


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


def test_context_keeps_each_contract_in_an_atomic_provenance_block():
    contracts = load_contracts(DATASET)
    results = search_contracts(contracts, "CPV 72000000-5", limit=2)
    context = format_context(results)

    for contract, _ in results:
        block = (
            f"BEGIN CONTRACT {contract.record_id}"
            + context.split(f"BEGIN CONTRACT {contract.record_id}", 1)[1].split(
                f"END CONTRACT {contract.record_id}", 1
            )[0]
            + f"END CONTRACT {contract.record_id}"
        )
        assert f"Source row: {contract.source_row}" in block
        assert contract.text in block
    assert context.count("BEGIN CONTRACT") == context.count("END CONTRACT")


def test_answer_prompt_contains_atomic_contract_boundaries(monkeypatch):
    captured = {}

    def fake_ask(*, prompt, system):
        captured["prompt"] = prompt
        captured["system"] = system
        return '{"answer":"unknown","record_ids":[],"confidence":"unknown"}'

    monkeypatch.setattr(assistant, "ask", fake_ask)
    assistant.answer_question(
        load_contracts(DATASET), "Qual o preço contratual do contrato com CPV 72000000-5?"
    )

    assert "BEGIN CONTRACT contrato-" in captured["prompt"]
    assert "END CONTRACT contrato-" in captured["prompt"]
    assert "return exactly one result" in captured["system"]
    assert "Never combine fields from different contract blocks" in captured["system"]


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


def test_persistent_rag_database_preserves_complete_contract_rows(tmp_path):
    contracts = load_contracts(DATASET)
    database_path = tmp_path / "contracts_rag.sqlite3"
    database = build_rag_database(contracts, database_path)

    assert isinstance(database, ContractRagDatabase)
    assert database_path.exists()
    results = search_contracts(
        contracts, "CPV 72000000-5", database=database
    )
    assert results
    result = results[0][0]
    original = next(
        contract for contract in contracts if contract.record_id == result.record_id
    )
    assert result.source_row == original.source_row
    assert result.fields == original.fields
    assert result.text == original.text


def test_persistent_rag_database_supports_rankings(tmp_path):
    contracts = load_contracts(DATASET)
    database = build_rag_database(contracts, tmp_path / "contracts_rag.sqlite3")
    results = search_contracts(
        contracts, "Quais os 3 maiores contratos?", database=database
    )

    assert len(results) == 3
    prices = [price for _, price in results]
    assert prices == sorted(prices, reverse=True)


def test_analytics_skill_counts_matching_contracts_without_llm(monkeypatch):
    monkeypatch.setattr(assistant, "ask", lambda **_: (_ for _ in ()).throw(
        AssertionError("analytics questions must not call the LLM")
    ))
    result = assistant.answer_question(
        load_contracts(DATASET), "How many contracts have CPV 72000000-5?"
    )

    assert result["answer"] == "14"
    assert len(result["record_ids"]) == 14
    assert len(result["source_rows"]) == 14


def test_analytics_skill_sorts_smallest_contracts():
    result = assistant.answer_question(
        load_contracts(DATASET), "What are the 3 smallest contracts?"
    )

    assert result["confidence"] == "high"
    assert result["answer"].count("\n") == 2
    assert len(result["source_rows"]) == 3


def test_singular_lowest_value_question_returns_one_contract():
    result = assistant.answer_question(
        load_contracts(DATASET), "Which contract has the less value?"
    )

    assert result["confidence"] == "high"
    assert len(result["record_ids"]) == 1
    assert result["answer"].count("\n") == 0


def test_search_combines_vector_scores_with_lexical_scores():
    contracts = load_contracts(DATASET)
    results = search_contracts(contracts, "requisitos da ENTI")
    assert results
    assert results[0][0].record_id == "contrato-0001"


def test_multiple_search_results_are_ordered_by_ascending_source_row():
    results = search_contracts(load_contracts(DATASET), "CPV 72000000-5", limit=3)

    source_rows = [contract.source_row for contract, _ in results]
    assert source_rows == sorted(source_rows)


def test_multiple_model_record_ids_are_ordered_by_ascending_source_row(monkeypatch):
    def fake_ask(*, prompt, system):
        return (
            '{"answer":"multiple","record_ids":["contrato-0120","contrato-0059"],'
            '"confidence":"high"}'
        )

    monkeypatch.setattr(assistant, "ask", fake_ask)
    result = assistant.answer_question(
        load_contracts(DATASET), "Which contracts mention CPV 72000000-5?"
    )

    assert result["record_ids"] == ["contrato-0059", "contrato-0120"]
    assert result["source_rows"] == [60, 121]


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
    assert result["answer"].startswith("1) ")
    assert len(result["record_ids"]) == 10
    contracts = load_contracts(DATASET)
    expected_rows = {
        contract.record_id: contract.source_row for contract in contracts
    }
    assert result["source_rows"] == [
        expected_rows[record_id] for record_id in result["record_ids"]
    ]


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
    assert json.loads(row[1])["source_rows"]
    assert row[2] == "contract_qa_v2"
    assert row[3] >= 0

    csv_lines = trace_csv.read_text(encoding="utf-8").splitlines()
    assert csv_lines[0].startswith("trace_id,created_at,input_text,output_json,")
    assert len(csv_lines) == 2
    assert "Quais os 10 maiores contratos?" in csv_lines[1]
