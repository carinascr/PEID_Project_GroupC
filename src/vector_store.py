"""Small local vector store for semantic contract retrieval.

The store uses TF-IDF vectors so it requires no external model download or
network service. SQLite keeps the indexed document vectors separate from the
read-only source dataset.
"""

from __future__ import annotations

import math
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from typing import Iterable


TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold())


@dataclass(frozen=True)
class VectorDocument:
    record_id: str
    weights: dict[str, float]
    norm: float


class ContractVectorStore:
    """An in-memory TF-IDF index backed by a local SQLite document store."""

    def __init__(self, documents: Iterable[tuple[str, str]]) -> None:
        rows = list(documents)
        self._connection = sqlite3.connect(":memory:")
        self._connection.execute(
            "CREATE TABLE documents (record_id TEXT PRIMARY KEY, text TEXT NOT NULL)"
        )
        self._connection.executemany(
            "INSERT INTO documents(record_id, text) VALUES (?, ?)", rows
        )
        self._idf = self._build_idf(rows)
        self._documents = tuple(
            self._make_document(record_id, text) for record_id, text in rows
        )

    @staticmethod
    def _build_idf(rows: list[tuple[str, str]]) -> dict[str, float]:
        document_count = len(rows)
        frequencies = Counter(
            token
            for _, text in rows
            for token in set(_tokens(text))
        )
        return {
            token: math.log((document_count + 1) / (count + 1)) + 1
            for token, count in frequencies.items()
        }

    def _make_document(self, record_id: str, text: str) -> VectorDocument:
        counts = Counter(_tokens(text))
        weights = {
            token: (count / sum(counts.values())) * self._idf[token]
            for token, count in counts.items()
        }
        return VectorDocument(record_id, weights, math.sqrt(sum(v * v for v in weights.values())))

    def search(self, query: str, limit: int = 5) -> list[tuple[str, float]]:
        query_counts = Counter(_tokens(query))
        if not query_counts:
            return []
        total = sum(query_counts.values())
        query_weights = {
            token: (count / total) * self._idf.get(token, 0.0)
            for token, count in query_counts.items()
            if token in self._idf
        }
        query_norm = math.sqrt(sum(value * value for value in query_weights.values()))
        if not query_norm:
            return []
        scored = []
        for document in self._documents:
            score = sum(
                query_weights.get(token, 0.0) * value
                for token, value in document.weights.items()
            )
            if score and document.norm:
                scored.append((document.record_id, score / (query_norm * document.norm)))
        return sorted(scored, key=lambda item: (-item[1], item[0]))[:limit]
