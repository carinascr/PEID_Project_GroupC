"""Command-line contract search assistant."""
import sys
import json
from pathlib import Path

try:
    from .assistant import answer_question
    from .contracts import load_contracts
except ImportError:
    from assistant import answer_question
    from contracts import load_contracts

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print("Usage: python src/app.py '<contract question>'")
        raise SystemExit(2)
    dataset = Path(__file__).parents[1] / "data" / "contratos_formatados.csv"
    print(json.dumps(answer_question(load_contracts(dataset), question), ensure_ascii=False))
