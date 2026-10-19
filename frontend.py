"""One-screen Streamlit interface for grounded contract questions."""

from pathlib import Path

import streamlit as st

from src.assistant import answer_question
from src.contracts import load_contracts
from src.rag_database import ContractRagDatabase, build_rag_database
from src.presentation import format_answer


ROOT = Path(__file__).parent
DATASET = ROOT / "data" / "contratos_formatados.csv"
RAG_DATABASE = ROOT / "data" / "contracts_rag.sqlite3"


@st.cache_resource
def get_contracts():
    return load_contracts(DATASET)


@st.cache_resource
def get_rag_database():
    contracts = get_contracts()
    if not RAG_DATABASE.exists():
        build_rag_database(contracts, RAG_DATABASE)
    return ContractRagDatabase(RAG_DATABASE)


st.set_page_config(page_title="Contract Assistant", page_icon="📄", layout="centered")
st.title("Contract Assistant")
st.caption("Search Portuguese public-procurement contracts with grounded answers.")
st.caption("Build: concise-answer-v1")

with st.form("contract_question", clear_on_submit=False):
    question = st.text_input(
        "Your question",
        placeholder="Ex.: Qual o preço contratual do contrato para evolução do vertical de Gestão de Ocorrências?",
    )
    submitted = st.form_submit_button(
        "Ask",
        type="primary",
    )

if submitted:
    if not question.strip():
        st.warning("Enter a question before asking.")
        st.stop()
    with st.spinner("Searching contracts and generating an answer..."):
        try:
            contracts = get_contracts()
            result = answer_question(
                contracts, question.strip(), database=get_rag_database()
            )
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            st.error(str(exc))
        else:
            st.subheader("Answer")
            st.markdown(format_answer(result["answer"]))
            st.caption(f"Confidence · {result['confidence']}")
            if result["record_ids"]:
                with st.expander("Sources"):
                    st.caption(
                        "CSV rows: "
                        + " · ".join(str(row) for row in result["source_rows"])
                    )
            else:
                st.info("No supporting contract record was retrieved.")
