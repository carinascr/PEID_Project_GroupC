from pathlib import Path

from contracts import format_context, load_contracts, search_contracts
from assistant import answer_question
from presentation import format_answer


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


def test_search_ranks_requested_number_of_largest_contracts():
    contracts = load_contracts(DATASET)
    results = search_contracts(contracts, "Quais os 10 maiores contratos?")
    assert len(results) == 10
    prices = [float(contract.fields["Preço Contratual"]) for contract, _ in results]
    assert prices == sorted(prices, reverse=True)


def test_largest_contract_question_is_answered_without_llm_unknown():
    result = answer_question(
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
