"""Grounded contract question answering."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

try:
    from .analytics_skill import run_analytics
    from .contracts import Contract, format_context, search_contracts
    from .llm import ask
    from .tracing import record_trace
except ImportError:
    from analytics_skill import run_analytics
    from contracts import Contract, format_context, search_contracts
    from llm import ask
    from tracing import record_trace

if TYPE_CHECKING:
    from .rag_database import ContractRagDatabase


PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "contract_qa_v2.md"


def answer_question(
    contracts: list[Contract],
    question: str,
    database: "ContractRagDatabase | None" = None,
) -> dict:
    started_at = time.perf_counter()
    analytics_result = run_analytics(contracts, question, database=database)
    if analytics_result is not None:
        record_trace(
            input_text=question,
            output=analytics_result,
            prompt_version=PROMPT_PATH.stem,
            latency_ms=(time.perf_counter() - started_at) * 1000,
        )
        return analytics_result
    results = search_contracts(contracts, question, database=database)
    if not results:
        result = {
            "answer": "unknown",
            "record_ids": [],
            "source_rows": [],
            "confidence": "unknown",
        }
    else:
        normalized_question = question.casefold()
        if "maior" in normalized_question and "contrat" in normalized_question:
            lines = [
                f"{index}) {contract.record_id} — "
                f"{contract.fields['Preço Contratual']} — "
                f"{contract.fields['Objeto do Contrato']}"
                for index, (contract, _) in enumerate(results, start=1)
            ]
            result = {
                "answer": "\n".join(lines),
                "record_ids": [contract.record_id for contract, _ in results],
                "source_rows": [contract.source_row for contract, _ in results],
                "confidence": "high",
            }
        else:
            response = ask(
                prompt=f"Question:\n{question}\n\nRetrieved context:\n{format_context(results)}",
                system=PROMPT_PATH.read_text(encoding="utf-8"),
            )
            try:
                result = json.loads(response)
            except json.JSONDecodeError as exc:
                raise ValueError("Model returned invalid JSON") from exc
            if not isinstance(result, dict) or not {"answer", "record_ids", "confidence"} <= result.keys():
                raise ValueError("Model response is missing required fields")
            valid_ids = {contract.record_id for contract, _ in results}
            if any(record_id not in valid_ids for record_id in result["record_ids"]):
                raise ValueError("Model cited a record outside retrieved context")
            records_by_id = {contract.record_id: contract for contract, _ in results}
            if len(result["record_ids"]) > 1:
                result["record_ids"] = sorted(
                    result["record_ids"],
                    key=lambda record_id: (
                        records_by_id[record_id].source_row,
                        record_id,
                    ),
                )
            result["source_rows"] = [
                records_by_id[record_id].source_row
                for record_id in result["record_ids"]
            ]

    record_trace(
        input_text=question,
        output=result,
        prompt_version=PROMPT_PATH.stem,
        latency_ms=(time.perf_counter() - started_at) * 1000,
    )
    return result
