---
name: format-answer
description: Format contract answers as fluent, readable, source-grounded responses with suitable tables or graphs.
---

Use this skill whenever an answer is prepared for display.

Rules:

- Lead with the answer; do not repeat the question.
- Write fluent, natural wording with correct grammar and a clear subject.
- Keep wording concise and factual; remove filler, repetition, and unnecessary
  preambles.
- Choose the clearest representation supported by the records:
  - For every question that suggests a comparison—such as comparing,
    versus, difference, higher/lower, largest/smallest, ranking, or
    "which is more/less"—use a graphical answer by default.
  - Use a Mermaid chart for comparison questions when the records contain
    explicit, comparable values. Label axes/series and preserve the source
    values; do not chart inferred or missing values.
  - If a comparison is requested but the records do not contain enough
    explicit comparable values for a truthful graph, use a compact Markdown
    comparison table and state the limitation briefly.
  - Use a compact Markdown table for two or more non-comparison records,
    counts by category, or other structured data.
  - Use short bullets for a small set of unrelated facts or when a table would
    make the answer harder to scan.
  - Use one polished sentence for a single factual answer.
- Show record IDs as source references, not as unexplained prose.
- Preserve source values exactly; never round, infer, or invent facts.
- Use `unknown` when the retrieved records do not support an answer.
- Keep confidence and sources visually secondary to the answer.
- Keep tables compact, give columns descriptive names, and sort rows according
  to the user’s requested order; otherwise use ascending source order.
- Put the conclusion before the table or graph when interpretation is needed.
- Do not use a table or graph to hide uncertainty or unsupported data.
