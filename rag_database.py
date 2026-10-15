"""Build and query a local SQLite FTS5 database from SourceData.csv.

The database stores one procurement record per document.  The original row is
kept as JSON metadata, while a labeled text representation is indexed for
retrieval-augmented generation workflows.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_CSV = Path(__file__).parent / "data" / "SourceData.csv"
DEFAULT_DATABASE = Path(__file__).parent / "data" / "procurement_rag.db"
TOKEN_RE = re.compile(r"[\wÀ-ÿ]+", re.UNICODE)


def _row_text(row: dict[str, str | None]) -> str:
    """Create searchable text without discarding the source column labels."""
    parts = []
    for column, value in row.items():
        value = (value or "").strip()
        if value:
            parts.append(f"{column}: {value}")
    return "\n".join(parts)


def _connect(database: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts "
            "USING fts5(document_id UNINDEXED, content, tokenize='unicode61 remove_diacritics 1')"
        )
    except sqlite3.OperationalError as exc:
        connection.close()
        raise RuntimeError("This SQLite build does not support FTS5.") from exc
    return connection


def build_database(
    csv_path: str | Path = DEFAULT_CSV,
    database_path: str | Path = DEFAULT_DATABASE,
) -> dict[str, Any]:
    """Convert the semicolon-delimited UTF-8 CSV into a fresh local database."""
    source = Path(csv_path)
    target = Path(database_path)
    if not source.is_file():
        raise FileNotFoundError(f"CSV file not found: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = _connect(target)
    try:
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            if not reader.fieldnames:
                raise ValueError("CSV has no header row.")
            columns = [column.strip() for column in reader.fieldnames]
            rows = []
            for row_number, source_row in enumerate(reader, start=1):
                row = {
                    column: (source_row.get(original) or "").strip()
                    for column, original in zip(columns, reader.fieldnames)
                }
                rows.append((row_number, _row_text(row), json.dumps(row, ensure_ascii=False)))
        with connection:
            connection.execute("DROP TABLE IF EXISTS documents")
            connection.execute("DROP TABLE IF EXISTS dataset_metadata")
            connection.execute(
                "CREATE TABLE documents ("
                "document_id INTEGER PRIMARY KEY, row_number INTEGER NOT NULL UNIQUE, "
                "content TEXT NOT NULL, metadata_json TEXT NOT NULL)"
            )
            connection.execute("DELETE FROM documents_fts")
            connection.executemany(
                "INSERT INTO documents(document_id, row_number, content, metadata_json) "
                "VALUES (?, ?, ?, ?)",
                [(number, number, content, metadata) for number, content, metadata in rows],
            )
            connection.executemany(
                "INSERT INTO documents_fts(document_id, content) VALUES (?, ?)",
                [(number, content) for number, content, _ in rows],
            )
            connection.execute(
                "CREATE TABLE dataset_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            connection.executemany(
                "INSERT INTO dataset_metadata(key, value) VALUES (?, ?)",
                [
                    ("source_file", str(source)),
                    ("row_count", str(len(rows))),
                    ("columns_json", json.dumps(columns, ensure_ascii=False)),
                ],
            )
        return {"database": str(target), "row_count": len(rows), "columns": columns}
    finally:
        connection.close()


def ensure_database(
    csv_path: str | Path = DEFAULT_CSV,
    database_path: str | Path = DEFAULT_DATABASE,
) -> dict[str, Any]:
    """Build the RAG database when it is missing or older than the CSV."""
    source = Path(csv_path)
    target = Path(database_path)
    if not target.exists() or target.stat().st_mtime < source.stat().st_mtime:
        return build_database(source, target)
    connection = _connect(target)
    try:
        try:
            row = connection.execute(
                "SELECT value FROM dataset_metadata WHERE key = 'row_count'"
            ).fetchone()
        except sqlite3.OperationalError:
            return build_database(source, target)
        if row is None:
            return build_database(source, target)
        return {"database": str(target), "row_count": int(row["value"])}
    finally:
        connection.close()


def _fts_query(query: str) -> str:
    tokens = TOKEN_RE.findall(query)
    if not tokens:
        raise ValueError("Search query must contain at least one word.")
    # Quoting each token prevents user input from becoming FTS syntax.
    return " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens[:32])


def search_database(
    query: str,
    database_path: str | Path = DEFAULT_DATABASE,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return the highest-ranked source rows for a natural-language query."""
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50.")
    connection = _connect(database_path)
    try:
        rows = connection.execute(
            "SELECT d.document_id, d.row_number, d.content, d.metadata_json, "
            "bm25(documents_fts) AS score "
            "FROM documents_fts JOIN documents d ON d.document_id = documents_fts.document_id "
            "WHERE documents_fts MATCH ? ORDER BY score LIMIT ?",
            (_fts_query(query), limit),
        ).fetchall()
        return [
            {
                "document_id": row["document_id"],
                "row_number": row["row_number"],
                "content": row["content"],
                "metadata": json.loads(row["metadata_json"]),
                "score": row["score"],
            }
            for row in rows
        ]
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert procurement CSV into a local RAG database.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    summary = build_database(args.csv, args.database)
    print(f"Created {summary['database']} with {summary['row_count']} documents.")
    print(f"Indexed {len(summary['columns'])} columns.")


if __name__ == "__main__":
    main()
