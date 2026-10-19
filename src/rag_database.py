"""Persistent SQLite knowledge base for contract-level retrieval."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Iterable

try:
    from .contracts import Contract
    from .vector_store import _tokens
except ImportError:
    from contracts import Contract
    from vector_store import _tokens


class ContractRagDatabase:
    """Read-only-at-query-time SQLite store containing complete source rows."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"RAG database not found: {self.path}")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def search(self, query: str, limit: int = 5) -> list[tuple[Contract, float]]:
        query_counts = Counter(_tokens(query))
        if not query_counts:
            return []
        with self._connect() as connection:
            idf = dict(
                connection.execute("SELECT token, value FROM idf").fetchall()
            )
            documents = connection.execute(
                "SELECT record_id, source_row, fields_json, text, weights_json, norm "
                "FROM contracts"
            ).fetchall()

        total = sum(query_counts.values())
        query_weights = {
            token: (count / total) * idf.get(token, 0.0)
            for token, count in query_counts.items()
            if token in idf
        }
        query_norm = math.sqrt(sum(value * value for value in query_weights.values()))
        if not query_norm:
            return []

        scored: list[tuple[Contract, float]] = []
        for record_id, source_row, fields_json, text, weights_json, norm in documents:
            weights = json.loads(weights_json)
            cosine = sum(
                query_weights.get(token, 0.0) * value
                for token, value in weights.items()
            )
            if cosine and norm:
                scored.append(
                    (
                        Contract(
                            record_id,
                            source_row,
                            json.loads(fields_json),
                            text,
                        ),
                        cosine / (query_norm * norm),
                    )
                )
        return sorted(scored, key=lambda item: (-item[1], item[0].record_id))[:limit]

    def rank_largest(self, limit: int = 5) -> list[tuple[Contract, float]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT record_id, source_row, fields_json, text "
                "FROM contracts"
            ).fetchall()
        ranked = []
        for record_id, source_row, fields_json, text in rows:
            fields = json.loads(fields_json)
            raw_price = fields.get("Preço Contratual", "").replace(",", ".")
            try:
                price = float(re.sub(r"[^\d.-]", "", raw_price))
            except ValueError:
                continue
            ranked.append((Contract(record_id, source_row, fields, text), price))
        return sorted(ranked, key=lambda item: (-item[1], item[0].record_id))[:limit]


def build_rag_database(
    contracts: Iterable[Contract], path: str | Path
) -> ContractRagDatabase:
    """Persist one complete contract per row and its TF-IDF representation."""
    rows = list(contracts)
    if not rows:
        raise ValueError("Cannot build a RAG database from no contracts")
    database_path = Path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = database_path.with_suffix(database_path.suffix + ".tmp")
    if temporary_path.exists():
        temporary_path.unlink()

    frequencies = Counter(
        token for contract in rows for token in set(_tokens(contract.text))
    )
    idf = {
        token: math.log((len(rows) + 1) / (count + 1)) + 1
        for token, count in frequencies.items()
    }

    with sqlite3.connect(temporary_path) as connection:
        connection.executescript(
            """
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE idf (token TEXT PRIMARY KEY, value REAL NOT NULL);
            CREATE TABLE contracts (
                record_id TEXT PRIMARY KEY,
                source_row INTEGER NOT NULL,
                fields_json TEXT NOT NULL,
                text TEXT NOT NULL,
                weights_json TEXT NOT NULL,
                norm REAL NOT NULL
            );
            """
        )
        connection.executemany(
            "INSERT INTO idf(token, value) VALUES (?, ?)", idf.items()
        )
        for contract in rows:
            counts = Counter(_tokens(contract.text))
            total = sum(counts.values())
            weights = {
                token: (count / total) * idf[token]
                for token, count in counts.items()
            }
            connection.execute(
                "INSERT INTO contracts VALUES (?, ?, ?, ?, ?, ?)",
                (
                    contract.record_id,
                    contract.source_row,
                    json.dumps(contract.fields, ensure_ascii=False),
                    contract.text,
                    json.dumps(weights),
                    math.sqrt(sum(value * value for value in weights.values())),
                ),
            )
        connection.executemany(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            [
                ("schema_version", "1"),
                ("document_count", str(len(rows))),
            ],
        )
        connection.commit()
    temporary_path.replace(database_path)
    return ContractRagDatabase(database_path)
