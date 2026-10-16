# Project rules

- Keep the product one-screen and focused on Portuguese public-procurement contract search.
- Route every model call through `src/llm.py`; never expose or print `.env`.
- Treat the supplied contract dataset as read-only source data and preserve record provenance.
- Never invent a contract fact. If retrieval does not support an answer, return `unknown`.
- Add or update automated tests for behavior changes and run the targeted test suite before declaring work complete.
- Keep prompts versioned in `prompts/` and evaluation artifacts in `evaluation/`.
