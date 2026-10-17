"""Append-only evaluation trace storage."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
import csv
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_TRACE_DB = Path(__file__).parents[1] / "evaluation" / "traces.sqlite3"
DEFAULT_TRACE_CSV = Path(__file__).parents[1] / "evaluation" / "traces.csv"


def trace_database_path() -> Path:
    """Return the configured trace database path."""
    return Path(os.environ.get("EVALUATION_TRACE_DB", DEFAULT_TRACE_DB))


def trace_csv_path() -> Path:
    """Return the configured CSV export path."""
    return Path(os.environ.get("EVALUATION_TRACE_CSV", DEFAULT_TRACE_CSV))


def _export_csv(database: Path) -> None:
    csv_path = trace_csv_path()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    columns = (
        "trace_id",
        "created_at",
        "input_text",
        "output_json",
        "prompt_version",
        "latency_ms",
    )
    with sqlite3.connect(database) as connection:
        rows = connection.execute(
            f"SELECT {', '.join(columns)} FROM traces "
            "ORDER BY created_at, trace_id"
        )
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=csv_path.parent,
                prefix=f".{csv_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                writer = csv.writer(temporary_file)
                writer.writerow(columns)
                writer.writerows(rows)
            os.replace(temporary_path, csv_path)
        finally:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()


def record_trace(
    *,
    input_text: str,
    output: Any,
    prompt_version: str,
    latency_ms: float,
) -> None:
    """Persist one evaluation trace and create the schema on first use."""
    database = trace_database_path()
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                input_text TEXT NOT NULL,
                output_json TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                latency_ms REAL NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO traces (
                trace_id, created_at, input_text, output_json,
                prompt_version, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                datetime.now(timezone.utc).isoformat(),
                input_text,
                json.dumps(output, ensure_ascii=False, sort_keys=True),
                prompt_version,
                latency_ms,
            ),
        )
    _export_csv(database)
