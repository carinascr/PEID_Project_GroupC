"""Grounded contract question answering."""

from __future__ import annotations

import json
from pathlib import Path

try:
    from .contracts import Contract, format_context, search_contracts
    from .llm import ask
except ImportError:
    from contracts import Contract, format_context, search_contracts
    from llm import ask


PROMPT_PATH = Path(__file__).parents[1] / "prompts" / "contract_qa_v1.md"


def answer_question(contracts: list[Contract], question: str) -> dict:
    results = search_contracts(contracts, question)
    if not results:
        return {
            "answer": "unknown",
            "record_ids": [],
            "confidence": "unknown",
        }
    normalized_question = question.casefold()
    if "maior" in normalized_question and "contrat" in normalized_question:
        lines = [
            f"{index}) {contract.record_id} — "
            f"{contract.fields['Preço Contratual']}"
            for index, (contract, _) in enumerate(results, start=1)
        ]
        return {
            "answer": "\n".join(lines),
            "record_ids": [contract.record_id for contract, _ in results],
            "confidence": "high",
        }
    response = ask(
        prompt=f"Question:\n{question}\n\nRetrieved context:\n{format_context(results)}",
        system=PROMPT_PATH.read_text(encoding="utf-8"),
    )
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError("Model returned invalid JSON") from exc
    if not isinstance(parsed, dict) or not {"answer", "record_ids", "confidence"} <= parsed.keys():
        raise ValueError("Model response is missing required fields")
    valid_ids = {contract.record_id for contract, _ in results}
    if any(record_id not in valid_ids for record_id in parsed["record_ids"]):
        raise ValueError("Model cited a record outside retrieved context")
    return parsed
