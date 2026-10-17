# Project starter

## Add your API key locally

You will receive your group's API key by e-mail. They go in a local `.env` file, which Git ignores.

1. Copy the example file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and paste the key from the e-mail:

   ```
   LLM_API_KEY=...
   ```

   The proxy URL and model name are already built in; you do not need to set them.

3. Save the file. Do not rename it, and do not move the key anywhere else (code, notes, chat, issues).

4. Check that Git is not tracking it. This command must **not** list `.env`:

   ```bash
   git status
   ```

Never commit `.env` or paste the key into any file that is committed. If you think the key has leaked, e-mail the instructor straight away.

## Contract assistant

The application searches the supplied contract snapshot and asks the course LLM
to answer using retrieved, cited records. Retrieval is hybrid: exact field and
ranking questions use the deterministic lexical path, while a local SQLite
TF-IDF vector index supplements lexical matching for semantic or paraphrased
questions. The source dataset remains read-only.

```bash
python src/app.py "Qual o preço contratual do contrato para evolução do vertical de Gestão de Ocorrências?"
```

The source file is currently named `data/contratos_formatados.csv`, but contains
an XLSX workbook. The loader detects the file signature and preserves its row
provenance. Run the offline retrieval evaluation with:

```bash
python evaluation/run_eval.py
pytest -q
```

Run the one-screen web frontend with:

```bash
streamlit run frontend.py
```

Each answered question is persisted in `evaluation/traces.sqlite3` and exported
to the readable `evaluation/traces.csv` file. Both are updated automatically
after every successful answer. The CSV export is regenerated from SQLite using
an atomic file replacement, so it does not contain partial writes.
The `traces` table stores the input question, JSON output, prompt version, UTC
timestamp, and elapsed latency in milliseconds. Set `EVALUATION_TRACE_DB` to
write traces to another SQLite file and `EVALUATION_TRACE_CSV` to choose the
matching CSV export path:

```bash
EVALUATION_TRACE_DB=/tmp/contract-traces.sqlite3 \
EVALUATION_TRACE_CSV=/tmp/contract-traces.csv \
python src/app.py "Que contratos têm CPV 72000000-5?"
```
