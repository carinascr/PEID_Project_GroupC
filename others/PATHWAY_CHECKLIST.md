# Capstone Project — Pathway Checklist

**Prompt Engineering and Interaction Design · Hugo Silva**

> **Progress legend:** `[x]` complete, `[~]` in progress or partially evidenced, `[ ]` not started, `[!]` blocked or requiring a decision.

## Assessment status

This document is the complete original pathway checklist, copied into the repository and annotated with the current project status. The current repository is the cloned `project-starter`; the supplied `data/contratos_formatados.csv` file contains an `.xlsx` workbook and is detected by file signature during ingestion.

**Current gate:** the implementation foundation is complete; full LLM evaluation, Copilot evidence capture, and submission rehearsal remain.

## Original checklist and progress

To successfully accomplish the project goals, you need to follow two tracks: the Copilot track is the set of files that steer your coding assistant. The App track is the product itself, generated using your coding assistant: input → LLM/Agents call → output, its data, and its evaluation.

This checklist was prepared to help you understand the boundaries of the project and organize its implementation. Copy this file into your repo so the coding assistant can help you check whether all milestones are accomplished.

Every example uses the project we ran in class: a ticket assistant — paste a customer ticket, get a category, an urgency, and a first-reply draft. Swap in your own idea. Tags such as (S4) point to the session that taught the item.

### M1 · Foundations

- [~] **Team ·** Split the roles. E.g. A builds the app, B creates and owns the database (if any), the demonstration input set and the evaluation golden set, C writes the Copilot files and keeps the report log.
  - **Evidence/status:** Roles have not yet been recorded in the repository.
- [x] **App ·** One-sentence problem statement. E.g. “Support agents paste a ticket and get its category, urgency and a reply draft in seconds.” Test: delete the LLM call — if a product remains, rethink the idea. If you cannot demo it in 90 seconds, cut scope.
  - **Proposed statement:** “A contract analyst searches 145 Portuguese public-procurement contract records and receives a grounded answer with supporting contract references in seconds.”
  - **Decision needed:** Approve this problem statement and the one-screen scope.
- [~] **App ·** Repo created from project-starter, group LLM key in .env, and python src/app.py returns an answer. E.g. your first commit can be “starter runs”. app.py and llm.py are only examples for the coding assistant; modify them as needed.
  - **Evidence/status:** The application and loader are implemented; offline tests pass. A live API-key run still needs to be captured.
- [x] **Copilot ·** Create AGENTS.md at the repo root with your always-on rules (S4). E.g. “All LLM calls go through ask() in src/llm.py · never open or print .env · synthetic data only · one screen, no login · implement tests and run the eval script before calling a change done.”
- [ ] **Copilot ·** Before/after evidence for AGENTS.md. Give Copilot the same request without and with the file; screenshot the difference. E.g. without it, Copilot created a second OpenAI client; with it, it reused ask().

### M2 · Running skeleton

- [x] **App ·** Input → LLM call → output, end to end on one screen. E.g. a text box and an “Analyse” button; the user gives an input (ticket), the app calls ask(system=PROMPT, prompt=ticket) and shows category, urgency and draft response. Ugly is fine; it must run.
- [x] **App ·** The prompt that does the work, in its own file (S2, S5). Use label definitions with boundaries, 2–3 examples, a fixed JSON output and an explicit “unknown” exit. E.g. your file name can be prompts/triage_v1.md; keep v1, v2… as iteration evidence.
- [ ] **[Optional] App ·** Data in the app’s internal database (S3). E.g. SQLite data/app.db with a clauses table (15 synthetic policy clauses the prompt pulls in as context) and a RAG engine that retrieves from clauses.
- [ ] **App ·** Evaluation traces, in the database or a file (S5, S6). E.g. a traces table or file logging each input, output, prompt version and latency.
- [x] **Copilot ·** At least one SKILL.md in .github/skills/<name>/ for a procedure you keep repeating (S4). E.g. run-eval, description: “Use when asked to evaluate or score the app: runs evaluation/run_eval.py and summarises pass rates per check.” Test: ask “how are we doing on the golden set?” without naming it — it should fire.
- [ ] **[Optional] Copilot ·** a sub-agent or an MCP server. E.g. a read-only .github/agents/reviewer.agent.md that flags ambiguous golden labels, or .vscode/mcp.json with a SQLite server to query app.db. Hooks are not required.

### M3 · Evaluation

- [ ] **App ·** Run 20+ realistic inputs and read every output — synthetic or public data only. Name what went wrong: this is your failure taxonomy (S5). E.g. “urgency inflated by angry wording (5/20) · draft promises a refund the policy forbids (3/20)”.
- [x] **App ·** Golden set of 20+ cases, labelled before you see a score (S5). E.g. evaluation/golden.csv with columns id, ticket, expected_category, expected_urgency, notes.
- [~] **App ·** Deterministic checks in code for everything with a right answer (S5). E.g. check 1 – output parses as JSON · check 2 – category is in the allowed list · check 3 – the evidence quote is a substring of the ticket · check 4 – draft ≤ 120 words · check 5 – category vs gold labels → precision and recall per class.
- [ ] **App ·** LLM-as-a-judge for what code cannot check (S6). One criterion per judge call, evidence quoted before a PASS/FAIL verdict, and an “unknown” exit. E.g. “Does the draft answer the customer’s actual request?” in evaluation/judge_prompt.md.
- [ ] **App ·** Judge checked against your own hand labels (S6). Pass your 20+ cases through the app, take the drafts from your traces, and hand-label about 20 of them PASS or FAIL in a separate file, e.g. evaluation/draft_labels.csv with columns id, draft, human_verdict, reason. Take PASS as the positive class and report TPR and TNR. E.g. “TPR 0.90, TNR 0.75 on 20 drafts”.

### M4 · Iterate and measure

- [ ] **App ·** One number you can defend: the metric, why that one, and what it does not cover. E.g. “We adopted macro-recall 0.78 on 24 cases because …; it does not tell us whether the reply drafts are any good.” It must be honest, not good.
- [ ] **App ·** One change tried, measured, and kept or abandoned with a reason. E.g. “prompt v3 added 8 examples: recall 0.78 → 0.79 at 3× the cost → abandoned, back to v2.”
- [ ] **Copilot ·** Evidence for every steering file: a commit or screenshot of what changed because of it. The report must show at least two (e.g. AGENTS.md + your skill). E.g. “run-eval fired on ‘score it’ and produced the same table every time.”

### M5 · Submit

- [ ] **Deck, 6 slides max, in this order:** the idea · the prompt · how you steered Copilot · failure taxonomy and golden set · your number · what you abandoned.
- [ ] **Report, 5 pages max, no appendices:** screenshots, the actual prompts, the dataset, the evaluation method and result, what did not work, and the repo link.
- [ ] **Repo made public at submission, link in the report, no commits after the deadline.** Check the secrets-scan workflow is green and .env is not in the history.
- [ ] **Demo rehearsed with a timer:** 8 minutes (about 4 of slides, 4 live) plus 2 for questions, and a backup recording.

## Mandatory requirements and measurable acceptance criteria

The Session 5 brief defines the product shape and submission constraints; the pathway checklist defines the implementation and evidence requirements. The following criteria turn them into checks that can be verified:

| ID | Acceptance criterion | Evidence / test |
|---|---|---|
| AC-01 | The product is a single-screen, text-in/text-out workflow in which the model is essential to the solution. | Run the app from a clean checkout; demonstrate input, model call, and output. Remove/bypass the model call and show that the intended product no longer works. |
| AC-02 | The end-to-end demo completes within 90 seconds for the core use case. | Timed rehearsal; record the elapsed time and use the same bounded scenario in the live demo. |
| AC-03 | The repository runs with the group key supplied only through ignored `.env`; no secret is committed or printed. | `git status`, secret scan workflow, history scan, and a local run using `.env`; `.env` must not appear in tracked files or history. |
| AC-04 | The core prompt is versioned in its own file and specifies boundaries, 2–3 examples, fixed JSON output, and an explicit `unknown` path. | Prompt review plus automated JSON-schema/contract tests, including an out-of-scope input. |
| AC-05 | The contracts knowledge base contains 145 source rows, preserves source provenance, and supports grounded retrieval. | Ingestion count check; every chunk has a stable record ID and source row reference; retrieval tests return the expected record for representative queries. |
| AC-06 | At least 20 realistic cases are run and every output is reviewed and assigned to a failure taxonomy. | Versioned run/traces file and failure taxonomy with counts summing to at least 20 cases. |
| AC-07 | A pre-labelled golden set contains at least 20 cases. | `evaluation/golden.csv` (or equivalent) exists before scoring and has IDs, inputs, expected labels, and notes. |
| AC-08 | Deterministic checks cover all objectively testable output constraints. | Automated tests for parseability, allowed labels, citation/evidence validity, required fields, and relevant numeric/text limits. |
| AC-09 | The LLM judge uses one criterion per call, quotes evidence before PASS/FAIL, and has an `unknown` exit. | Judge prompt tests and saved judge traces. |
| AC-10 | Judge performance is compared with hand labels using TPR and TNR on about 20 cases. | Separate hand-label file, reproducible calculation, and reported TPR/TNR with denominators. |
| AC-11 | One primary metric is selected with a defensible rationale and limitations. | Report states the metric, why it fits the task, the measured value, denominator, and what it does not cover. |
| AC-12 | At least one prompt or implementation change is measured and explicitly kept or abandoned. | Before/after evaluation results, cost/latency where relevant, and decision recorded in the report and git history. |
| AC-13 | At least two Copilot steering surfaces have before/after evidence. | AGENTS.md plus a skill (or another approved steering surface), with screenshots or commits showing the effect. |
| AC-14 | Submission artifacts satisfy the format limits. | Deck has at most 6 slides in the required order; report has at most 5 pages and no appendix; repo link is present. |
| AC-15 | Presentation and submission are operationally ready. | Eight-minute timed rehearsal plus two minutes for questions, backup recording, public repo, green secrets scan, and no post-deadline commits. |

## Current assessment

### Starter repository

The cloned repository is a minimal Python starter:

- `src/app.py` joins command-line arguments and calls `llm.ask`.
- `src/llm.py` centralizes the OpenAI-compatible client, loads `.env`, and defaults to the course proxy/model.
- `requirements.txt` currently contains `openai` and `python-dotenv`.
- `tests/`, `evaluation/`, and `data/` are placeholders; no application tests, evaluation runner, prompt files, RAG store, or Copilot steering files are present yet.
- The repository README already documents the secret-handling rule. The local `.env` is ignored and must never be copied into committed documentation.

### Dataset format and relevant columns

The supplied file is `data/contratos_formatados.xlsx` (145 rows × 34 columns), not a CSV. It should be treated as a source snapshot and converted to a normalized, versioned ingestion artifact rather than edited in place.

**Primary retrieval and answer fields**

- `Objeto do Contrato`: the most important natural-language search text.
- `CPV`, `CPV Designação`, and `CPV Valor`: classification and value descriptors.
- `Tipo de Procedimento`, `Tipo(s) de Contrato`, `Regime`, `Fundamentação`, `Critérios Materiais`: procedural/legal context.
- `Entidade(s) Adjudicante(s)` and `Entidade(s) Adjudicatária(s)`: buyer and supplier entities.
- `Preço Contratual`, `Preço Total Efetivo`, and `Prazo de Execução`: commercial and duration facts.
- `Data de Publicação`, `Data de Celebração do Contrato`, and `Data de Fecho do Contrato`: temporal filters and answer evidence.
- `Local de Execução`: geographic filters.
- `N.º registo do Acordo Quadro`, `Descrição do Acordo Quadro`, `Procedimento Centralizado`, `Ligação para Peças do Procedimento`, and `CCP`: agreement/provenance context.

**Secondary or conditional fields**

`Causa de Extinção do Contrato`, `Causas das Alterações ao Prazo`, `Causas das Alterações ao Preço`, `Medidas especiais`, and `Lista de Fornecedores (cocontratantes)` should be retained but only surfaced when populated. They are useful for exception and amendment questions.

**Fields requiring explicit handling**

`Estado`, `Aquisição ao Abrigo de Acordo Quadro de outro Estado-membro da UE`, `Valor Estimado Procedimento`, and `groupMembers` are entirely null in this snapshot. `occurrences` is always `False`; it adds no retrieval value. `CPV Tipo` is always `Principal`; retain as provenance if desired, but do not use it as a discriminating feature.

### Data-quality findings

- 145 rows and 34 columns; no fully duplicated rows were found.
- 88 rows have no close date, effective total price, or extinction cause; this may be valid for active/unclosed contracts and must not be imputed as zero or “not applicable”.
- 142 rows have no “Causas das Alterações ao Prazo”; 144 have no price-change cause.
- 72 rows have no procedure-pieces link; links should be validated as optional URLs, not required retrieval content.
- 4 columns are entirely null; one additional boolean-like field is entirely null and one is constant false. These should be excluded from embeddings while preserving the raw snapshot.
- Contract price, CPV value, and publication/signature dates are populated for all 145 rows. Contract prices range from 4,125 to 200,000 in the source values; no negative contract prices were found.
- There are 12 duplicate contract-object values after case/whitespace normalization. These are not duplicate rows; retrieval must include a stable row ID and display disambiguating metadata.
- Publication is later than signature in 114 records. This may reflect source semantics or a data issue and must be flagged rather than silently corrected.
- Portuguese accents, legal citations, currency-like numeric values, boolean values, and date/duration strings require type-aware normalization. Keep original values for citations and auditability.

## RAG knowledge-base recommendation

### Ingestion and normalization

1. Preserve the workbook under `data/` as the immutable source snapshot and record its filename, ingestion timestamp, row count, and a content hash.
2. Export a normalized UTF-8 CSV or JSONL artifact with one record per source row and a stable ID such as `contrato-0001`. Do not fabricate missing values.
3. Normalize column names to stable machine names while retaining a `source_fields` map. Parse dates as ISO dates, prices as numeric values plus source currency metadata if available, booleans as nullable booleans, and durations into a structured value/unit plus original text.
4. Build a canonical searchable text representation in Portuguese from populated fields, using explicit labels, for example `Objeto do contrato: ...`, `Entidade adjudicante: ...`, and `Preço contratual: ...`.
5. Keep structured metadata beside each text record: record ID, CPV, buyer, supplier, procedure, contract type, dates, price, location, source row, and source file.

### Retrieval and grounding

- Start with one chunk per contract row; 145 rows are small enough to avoid arbitrary chunk splitting. If a row becomes too long, split by labelled field groups and repeat the stable record ID in every chunk.
- Use hybrid retrieval: lexical matching for exact legal citations, CPV codes, names, and IDs, plus embeddings for natural-language descriptions. Apply metadata filters for date, location, procedure, entity, and price where possible.
- Retrieve a small top-k set (initially 3–5), include the record ID and selected source fields in the prompt, and require the model to cite returned record IDs.
- If retrieval scores are below a threshold or no record supports the answer, return `unknown` rather than inventing a contract, value, date, or legal interpretation.
- Test retrieval separately from generation using labelled queries: expected record IDs, acceptable top-k rank, and no unsupported citations.
- Display source references in the UI so a reviewer can inspect the underlying contract row. Do not embed the optional external procedure links as if they were verified document contents.

## Proposed 12-phase implementation sequence

This sequence is the proposed operational interpretation of the agreed 12-phase workflow. It is intentionally ordered so evaluation and steering evidence exist before the final implementation is declared complete.

1. **Scope and roles:** approve the problem statement, one-screen boundary, team responsibilities, demo scenario, and decision log.
2. **Repository and safety baseline:** verify the starter run, `.env` handling, secrets scan, branch state, and a minimal test command.
3. **Dataset ingestion contract:** define source hash, stable IDs, normalized schema, missing-value policy, and provenance requirements.
4. **Knowledge-base build:** implement workbook-to-JSONL/CSV normalization and a deterministic loader; validate the 145-row count.
5. **Retrieval baseline:** implement lexical/hybrid retrieval with metadata filters and retrieval-level tests before adding generation.
6. **Prompt contract:** create `prompts/contract_qa_v1.md` with boundaries, examples, fixed JSON, citations, and `unknown`; add prompt/schema tests.
7. **One-screen skeleton:** connect one input to retrieval, `ask()`, and a grounded output with visible sources; preserve the single-screen constraint.
8. **Traceability and observability:** record input, retrieved IDs, prompt version, output, latency, errors, and model metadata without secrets.
9. **Evaluation assets:** create 20+ realistic cases, pre-label the golden set, define the failure taxonomy, and add deterministic checks.
10. **Judge and iteration:** add criterion-specific LLM judging, hand labels, TPR/TNR calculations, and one measured prompt/retrieval change.
11. **Copilot steering and evidence:** add `AGENTS.md` and a repeatable `.github/skills/<name>/SKILL.md`; capture before/after evidence and commits/screenshots.
12. **Submission hardening:** run unit tests and evaluation, finalize report/deck, document risks and abandonment decisions, run secret scanning, rehearse the timed demo, and freeze the public repository.

### Planned automated tests and evaluation

- **Unit tests:** normalization of dates, prices, booleans, durations, nulls, accents, duplicate object titles, stable IDs, and source provenance.
- **Retrieval tests:** exact CPV/legal/entity queries, semantic object queries, metadata filters, expected record IDs in top-k, and no-result behavior.
- **Output contract tests:** valid JSON, required fields, allowed values, source IDs that exist in retrieved context, no unsupported numeric/date claims, and explicit `unknown`.
- **Trace tests:** required trace fields are present, latency is numeric, prompt version is recorded, and secrets are absent.
- **Evaluation runner:** reproducibly executes the golden set, runs deterministic checks, optionally calls one judge criterion at a time, and reports results with denominators.
- **Regression gate:** the kept change must not regress the primary metric or violate retrieval/source-citation checks; any accepted trade-off must be recorded.

### Copilot steering evidence to capture

At minimum, retain:

1. A before/after example showing how `AGENTS.md` changes a request, such as reusing `ask()` and not exposing `.env`.
2. A `run-eval` skill invocation triggered by a natural request such as “how are we doing on the golden set?”, with the resulting stable evaluation table.
3. Commit or screenshot references in the report connecting each steering file to an observable repository or workflow change.

## Risks and mitigations

| Risk | Impact | Mitigation / acceptance gate |
|---|---|---|
| Workbook is treated as a CSV without an explicit conversion step. | Broken ingestion or irreproducible data. | Keep the `.xlsx` snapshot, hash it, and generate a versioned normalized artifact with a row-count test. |
| Sparse/null fields are imputed or embedded as facts. | Hallucinated contract status, prices, or amendments. | Preserve nulls, omit empty labelled fields from canonical text, and test `unknown` behavior. |
| Publication/signature ordering is “corrected” silently. | Loss of source fidelity and misleading legal answers. | Preserve source dates, flag the anomaly, and avoid inferred corrections. |
| Similar contract objects retrieve the wrong row. | Unsupported answer or citation. | Stable IDs, disambiguating metadata, hybrid retrieval, and top-k retrieval tests. |
| LLM invents a legal conclusion or source. | High-trust factual error. | Constrained prompt, source-ID citations, explicit refusal/`unknown`, deterministic citation checks, and judge review. |
| Scope expands beyond a one-screen demo. | Missed deadline and weak evaluation. | Freeze the core use case and reject nonessential UI/features until M5 is complete. |
| Copilot changes are not reproducible or evidenced. | Loss of marks for steering/iteration evidence. | Use versioned steering files, small commits, screenshots, and a report evidence log. |
| Secrets leak through traces, screenshots, or git history. | Security and submission failure. | Never log environment values, run secrets scan, inspect history, and verify `.env` is ignored/untracked. |
| Evaluation is created after implementation or labels are influenced by scores. | Invalid measurement. | Label the 20+ golden cases before scoring and record the evaluation artifact commit. |

## Recommended next steps for approval

1. Approve or revise the proposed contract-search problem statement and one-screen scope.
2. Confirm the workbook-to-normalized-artifact decision and whether answers should be Portuguese, English, or bilingual.
3. Assign team roles and nominate the 20+ golden-set questions before implementation.
4. Approve the 12-phase sequence and the acceptance criteria in this document.
5. After approval, begin Phase 1 only; no application code should be changed before that approval gate.
