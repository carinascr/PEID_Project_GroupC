"""Command-line contract search assistant."""
import sys
import json
from pathlib import Path

try:
    from .assistant import answer_question
    from .contracts import load_contracts
    from .rag_database import ContractRagDatabase, build_rag_database
except ImportError:
    from assistant import answer_question
    from contracts import load_contracts
    from rag_database import ContractRagDatabase, build_rag_database

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print("Usage: python src/app.py '<contract question>'")
        raise SystemExit(2)
    dataset = Path(__file__).parents[1] / "data" / "contratos_formatados.csv"
    contracts = load_contracts(dataset)
    database_path = dataset.with_name("contracts_rag.sqlite3")
    if not database_path.exists():
        build_rag_database(contracts, database_path)
    database = ContractRagDatabase(database_path)
    print(
        json.dumps(
            answer_question(contracts, question, database=database),
            ensure_ascii=False,
        )
    )
