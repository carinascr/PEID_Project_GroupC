"""Deterministic calculations over complete contract records."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

try:
    from .rag_database import ContractRagDatabase
    from .contracts import Contract, search_contracts
except ImportError:
    from rag_database import ContractRagDatabase
    from contracts import Contract, search_contracts


@dataclass(frozen=True)
class AnalyticsRequest:
    operation: str
    filter_query: str
    limit: int


_COUNT_WORDS = (
    "how many",
    "count",
    "quantos",
    "quantas",
    "quantidade",
    "numero de",
    "número de",
)
_LARGEST_WORDS = ("biggest", "largest", "highest", "maior", "maiores")
_SMALLEST_WORDS = (
    "smallest",
    "lowest",
    "cheapest",
    "least",
    "lower",
    "less",
    "menor",
    "menores",
)
_STOP_WORDS = {
    "a", "as", "are", "biggest", "cheapest", "como", "con", "contract",
    "contracts", "count", "das", "de", "do", "dos", "how", "many", "maior",
    "maiores", "menor", "menores", "most", "number", "of", "os", "quais",
    "quantas", "quantidade", "quantos", "the", "to", "top", "what", "which",
    "largest", "highest", "lowest", "smallest", "maior", "maiores", "menor",
    "menores", "biggest", "cheapest", "has", "have", "with", "value",
    "valor", "less", "lower", "least",
}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return "".join(
        char for char in normalized if not unicodedata.combining(char)
    )


def detect_request(question: str) -> AnalyticsRequest | None:
    """Classify calculation wording and retain only meaningful filter terms."""
    normalized = _normalize(question)
    is_count = any(phrase in normalized for phrase in _COUNT_WORDS)
    is_largest = any(word in normalized for word in _LARGEST_WORDS)
    is_smallest = any(word in normalized for word in _SMALLEST_WORDS)
    if sum((is_count, is_largest, is_smallest)) != 1:
        return None

    number = re.search(r"\b(\d+)\b", normalized)
    if number:
        limit = int(number.group(1))
    else:
        singular_contract = bool(
            re.search(r"\b(contract|contrato)\b", normalized)
        )
        plural_contract = bool(
            re.search(r"\b(contracts|contratos)\b", normalized)
        )
        limit = 1 if singular_contract and not plural_contract else 5
    filter_terms = [
        token
        for token in re.findall(r"\w+", normalized)
        if token not in _STOP_WORDS and not token.isdigit()
    ]
    operation = "count" if is_count else "largest" if is_largest else "smallest"
    return AnalyticsRequest(operation, " ".join(filter_terms), limit)


def _price(contract: Contract) -> float | None:
    raw = contract.fields.get("Preço Contratual", "").replace(",", ".")
    cleaned = re.sub(r"[^\d.-]", "", raw)
    try:
        return float(cleaned)
    except ValueError:
        return None


def run_analytics(
    contracts: list[Contract],
    question: str,
    database: "ContractRagDatabase | None" = None,
) -> dict | None:
    """Run a supported calculation, or return None for normal QA questions."""
    request = detect_request(question)
    if request is None:
        return None

    cpv_match = re.search(r"\b\d{8}-\d\b", _normalize(question))
    if request.filter_query:
        if cpv_match:
            candidates = [
                contract
                for contract in contracts
                if contract.fields.get("CPV") == cpv_match.group(0)
            ]
        else:
            candidates = [
                contract
                for contract, _ in search_contracts(
                    contracts,
                    request.filter_query,
                    limit=len(contracts),
                    database=database,
                )
            ]
    else:
        candidates = list(contracts)

    if request.operation == "count":
        return {
            "answer": str(len(candidates)),
            "record_ids": [contract.record_id for contract in candidates],
            "source_rows": [contract.source_row for contract in candidates],
            "confidence": "high",
        }

    priced = [
        (contract, value)
        for contract in candidates
        if (value := _price(contract)) is not None
    ]
    reverse = request.operation == "largest"
    ranked = sorted(priced, key=lambda item: (-item[1] if reverse else item[1], item[0].record_id))
    selected = ranked[: request.limit]
    lines = [
        f"{index}) {contract.fields['Preço Contratual']} — "
        f"{contract.fields['Objeto do Contrato']}"
        for index, (contract, _) in enumerate(selected, start=1)
    ]
    return {
        "answer": "\n".join(lines) if lines else "unknown",
        "record_ids": [contract.record_id for contract, _ in selected],
        "source_rows": [contract.source_row for contract, _ in selected],
        "confidence": "high" if selected else "unknown",
    }
