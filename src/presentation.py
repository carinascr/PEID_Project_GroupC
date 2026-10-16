"""Minimal, consistent presentation formatting for assistant answers."""

from __future__ import annotations

import re


_RANKED_LINE = re.compile(
    r"^(\d+)\)\s+(\S+)\s+—\s+(\S+)(?:\s+—\s+(.+))?$"
)


def _summary(text: str, limit: int = 68) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"


def format_answer(answer: str) -> str:
    """Return display-ready Markdown without changing factual values."""
    answer = answer.strip()
    ranked_lines = [_RANKED_LINE.match(line.strip()) for line in answer.splitlines()]
    if ranked_lines and all(match for match in ranked_lines):
        rows = [
            f"| {match.group(1)} | {_summary(match.group(4) or match.group(2))} | "
            f"{match.group(3)} |"
            for match in ranked_lines
        ]
        return "\n".join(
            ["| # | Contract | Contract price |", "|---:|---|---:|", *rows]
        )
    return answer
