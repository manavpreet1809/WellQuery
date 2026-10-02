# WellQuery commit progress

## Day 2 — original MediBot baseline

Imported Manavpreet Singh's `app`, `llm`, `templates`, `static`, and original requirements from the supplied MediBot folder. `medibot-baseline.json` records SHA-256 hashes of the imported files so later changes can be distinguished from the original work.

Databricks notebooks, training helpers, caches, and empty deployment stubs were not imported. The original external serving endpoints remain dependencies of the baseline. No model weights, third-party health documents, or secrets were imported.

Validation: Python files parse successfully; imported files were checked for common GitHub, Hugging Face, and Databricks token patterns. This is a baseline snapshot, not a claim that live Databricks inference has been tested. The next commit will address startup configuration, missing web dependencies, and failure handling.

## Day 3 — stabilize the chat flow

Added credential-free startup, explicit scripted demo mode, a single shared classify/retrieve/answer pipeline, bounded request parameters, rejection of missing full-text evidence, generic upstream errors, and offline dependency injection tests. Removed external UI assets and HTML string interpolation; both user and model messages are rendered as text. Added loading/error handling, local setup instructions, and separate optional model dependencies.

Validation: 12 offline API tests passed, including the complete pipeline with injected classifier, retriever, and generator. No real health-answer quality or live Databricks/model inference is claimed. The small frontend change is for baseline operation; the evidence panel and visual polish remain later work.

## Day 4 — document ingestion

Added a validated source catalogue, explicit permission records, robots-aware downloads, cached retrieval receipts, article-section extraction, bounded overlapping word chunks, and transactional SQLite storage. Three NIDDK articles form the starter collection; the intended 15–20 document collection remains future expansion. This interim store needs neither Databricks nor a database server. Embeddings and local search are the next planned commit, not part of this stage.

Validation: all 24 offline tests pass. Live ingestion produced 38 chunks across 3 documents; the cached rerun changed 0 documents. Tests cover attribution, sections, chunk boundaries, changed content, metadata changes, duplicate/unapproved sources, missing selectors, empty content, stale receipts, and robots denial. One upstream Starlette/AnyIO deprecation warning remains; tests succeed. Remote inference and browser interaction have not been verified.

## Remaining daily targets

5. Keyword and vector search over the local documents.
6. Hybrid retrieval and question routing comparison.
7. Passage citations and prototype response safeguards.
8. Expandable evidence panel and interface polish.
9. Manually checked evaluation set and comparative results.
10. Results dashboard, final documentation, and demo.
