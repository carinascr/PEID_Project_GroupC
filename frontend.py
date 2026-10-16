"""One-screen Streamlit interface for grounded contract questions."""

from pathlib import Path

import streamlit as st

from src.assistant import answer_question
from src.contracts import load_contracts, search_contracts


ROOT = Path(__file__).parent
DATASET = ROOT / "data" / "contratos_formatados.csv"


@st.cache_resource
def get_contracts():
    return load_contracts(DATASET)


st.set_page_config(page_title="Contract Assistant", page_icon="📄", layout="centered")
st.title("Contract Assistant")
st.caption("Search Portuguese public-procurement contracts with grounded answers.")
st.caption("Build: deterministic-ranking-v2")

question = st.text_area(
    "Your question",
    placeholder="Ex.: Qual o preço contratual do contrato para evolução do vertical de Gestão de Ocorrências?",
    height=110,
)

if st.button("Ask", type="primary", disabled=not question.strip()):
    with st.spinner("Searching contracts and generating an answer..."):
        try:
            contracts = get_contracts()
            normalized_question = question.casefold()
            if "maior" in normalized_question and "contrat" in normalized_question:
                ranked = search_contracts(contracts, question.strip())
                result = {
                    "answer": "\n".join(
                        f"{index}) {contract.record_id} — "
                        f"{contract.fields['Preço Contratual']}"
                        for index, (contract, _) in enumerate(ranked, start=1)
                    ),
                    "record_ids": [contract.record_id for contract, _ in ranked],
                    "confidence": "high",
                }
            else:
                result = answer_question(contracts, question.strip())
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            st.error(str(exc))
        else:
            st.subheader("Answer")
            st.write(result["answer"])
            st.caption(f"Confidence: {result['confidence']}")
            if result["record_ids"]:
                st.subheader("Sources")
                for record_id in result["record_ids"]:
                    st.code(record_id)
            else:
                st.info("No supporting contract record was retrieved.")
