# Prompt History

This file records the prompt-driven development history of the Contract
Assistant project.

## 1. Repository setup

**Request:** Clone `https://github.com/hugosaisse/project-starter.git`.

**Result:**

- Project starter repository obtained and inspected.
- Existing starter files included a minimal CLI app, centralized LLM client,
  requirements, and placeholder data/evaluation/test directories.

## 2. Requirements and dataset assessment

**Request:** Review the NOVA IMS Session 5 Project Brief and Capstone Project
Pathway Checklist, inspect the starter repository, analyze the contracts data,
and propose an implementation plan.

**Result:**

- Created [`docs/PATHWAY_CHECKLIST.md`](./PATHWAY_CHECKLIST.md).
- Copied the complete M1–M5 checklist into the repository.
- Added progress tracking.
- Extracted measurable acceptance criteria.
- Documented the proposed 12-phase implementation sequence.
- Documented risks, testing requirements, evaluation requirements, and Copilot
  steering evidence.
- Identified the supplied contracts file as an XLSX workbook despite its
  `.csv` filename.
- Profiled 145 records and 34 columns.
- Identified null fields, duplicate normalized contract descriptions, date
  ordering anomalies, and provenance requirements.

## 3. Contract assistant foundation

**Request:** Implement the approved project plan without leaving the project at
the assessment stage.

**Result:**

- Added [`AGENTS.md`](../AGENTS.md) with project rules.
- Added the reusable Copilot evaluation skill at
  [`format-answer/SKILL.md`](../.github/skills/format-answer/SKILL.md) later in
  the project and the evaluation skill at
  [`run-eval/SKILL.md`](../.github/skills/run-eval/SKILL.md).
- Added format-detecting contract ingestion in
  [`src/contracts.py`](../src/contracts.py).
- Added stable contract IDs and source-row provenance.
- Added lexical retrieval with ranking and metadata text.
- Added grounded LLM question answering in
  [`src/assistant.py`](../src/assistant.py).
- Added the versioned prompt at
  [`prompts/contract_qa_v1.md`](../prompts/contract_qa_v1.md).
- Updated the CLI in [`src/app.py`](../src/app.py).
- Added a 20-case golden set at
  [`evaluation/golden.csv`](../evaluation/golden.csv).
- Added the offline evaluation runner at
  [`evaluation/run_eval.py`](../evaluation/run_eval.py).
- Added unit tests in [`tests/test_contracts.py`](../tests/test_contracts.py).

## 4. Initial validation

The initial implementation was validated with:

```text
retrieval_cases=20 passed=20 pass_rate=100.00%
3 passed
```

The CLI successfully answered a contract-price question with a grounded
record ID.

## 5. Frontend

**Request:** Run the frontend, then add one when it was discovered that the
starter repository only contained a CLI.

**Result:**

- Added the one-screen Streamlit application in
  [`frontend.py`](../frontend.py).
- Added Streamlit to [`requirements.txt`](../requirements.txt).
- Added frontend usage instructions to [`README.md`](../README.md).
- Reused the existing retrieval and LLM path.
- Added answer, confidence, and source display.
- Verified the local health endpoint:

```text
Frontend health: ok
```

## 6. Import defect

**Reported problem:** Streamlit raised:

```text
ModuleNotFoundError: No module named 'contracts'
```

**Fix:**

- Added [`src/__init__.py`](../src/__init__.py).
- Added package-compatible and direct-script-compatible imports in
  [`src/assistant.py`](../src/assistant.py) and [`src/app.py`](../src/app.py).

**Validation:**

```text
CLI response returned correctly
3 passed
Frontend health: ok
```

## 7. Ranking-query defect

**Reported problem:** The question `Quais os 10 maiores contratos?` returned
`unknown`.

**Fix:**

- Added deterministic ranking by `Preço Contratual`.
- Added support for requested result counts such as 10.
- Prevented the LLM from deciding whether a deterministic ranking query was
  answerable.
- Added a regression test for the top-10 result.

**Result:**

```text
1) contrato-0035 — 200000
2) contrato-0121 — 200000
3) contrato-0017 — 182760
...
10) contrato-0097 — 79439.83
```

## 8. Stale frontend troubleshooting

**Reported problem:** The browser continued to show `unknown` after the
ranking fix.

**Investigation:**

- Confirmed the backend returned the correct result.
- Inspected the active Streamlit process and port.
- Stopped stale Streamlit processes.
- Restarted the server on port 8501.
- Added a temporary visible build marker:
  `Build: deterministic-ranking-v2`.

**Additional hardening:**

- Added a frontend-level deterministic ranking path.
- Restarted and health-checked the current server.

## 9. Answer formatting skill

**Request:** Make answers formatted, simple, minimalistic, and aesthetic.

**Result:**

- Added [`src/presentation.py`](../src/presentation.py).
- Added the reusable
  [`format-answer` skill](../.github/skills/format-answer/SKILL.md).
- Ranked answers now render as compact Markdown tables.
- Single-value answers remain concise.
- Sources are shown in an expandable section.
- Confidence is visually secondary.
- Added the build marker `Build: concise-answer-v1`.

**Validation:**

```text
6 passed
Frontend health: ok
```

## 10. Contract-column improvement

**Request:** Replace contract IDs in the table with a minimal summary of what
each contract is about.

**Result:**

- The `Contract` column now uses `Objeto do Contrato`.
- Long descriptions are normalized and truncated with `…`.
- Record IDs remain available in the Sources section.
- The answer formatter preserves prices and source values exactly.

Example:

```text
Aquisição de Serviços de Cloud no âmbito da operação Aveiro Media…
```

**Validation:**

```text
7 passed
Frontend health: ok
```

## 11. Enter-key submission

**Request:** Pressing Enter should behave like clicking Ask.

**Initial implementation:**

- Wrapped the question field and Ask control in a Streamlit form.
- Used a single-line input and form submission.

**Reported defect:** The Ask button appeared disabled while entering a
question, so Enter did not activate an enabled submit target.

**Final fix:**

- Removed the dynamic disabled state from the Ask button.
- Added validation after submission.
- Empty submissions show a warning.
- Non-empty submissions run the same path for Enter and mouse clicks.

**Validation:**

```text
7 passed
Frontend health: ok
```

## 12. Branch

**Request:** Create a branch called “1st steps”.

**Result:**

- Created and checked out the Git-compatible branch:

```text
1st-steps
```

Git branch names cannot contain spaces, so the requested name was normalized to
use a hyphen.

## Current state

- Branch: `1st-steps`
- Frontend: Streamlit on port 8501
- Dataset: 145 source contract records
- Offline retrieval evaluation: 20/20 passing
- Unit tests: 7 passing
- Frontend health check: passing
- Main remaining project work: complete trace logging, LLM-as-a-judge
  evaluation, hand-labelled evaluation comparison, measured prompt iteration,
  Copilot evidence capture, and final submission artifacts.
