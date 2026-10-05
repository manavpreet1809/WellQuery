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

## Day 5 — keyword and vector retrieval

Added BM25 keyword search and optional MiniLM semantic embeddings with exact cosine ranking. A pinned model revision, persisted vector snapshot, metadata fingerprints, and stale-index checks make changed source content explicit. Search returns full passages and attribution through a CLI. Tests use deterministic vectors; they do not claim semantic quality. Keyword search remains independent of model dependencies. Full held-out retrieval evaluation remains Day 9.

Day 5 verification: 33 offline tests passed. The actual pinned MiniLM model downloaded successfully and indexed all 38 existing chunks. Live keyword and local vector smoke queries returned source passages; this confirms operation, not accuracy on a verified evaluation set.

## Day 6 — hybrid retrieval and local routing baseline

Added reciprocal rank fusion, optional category routing, and a validated `/search` endpoint with metadata, component ranks, latency, and explicit empty-result reasons. The original Databricks classifier is still available in its remote flow. Because trained local artifacts are not supplied, the local comparator uses documented cue-based rules instead of claiming to reproduce that model. Medication search with routing reports missing coverage in the current condition-only corpus.

Verification: 43 offline tests pass, covering hand-computed fusion scores, mixed/unknown routing, category filtering, API validation, missing stores, vector freshness, and previous ingestion/API behavior. Real keyword, vector, and hybrid endpoint smoke tests run against 38 indexed chunks. These checks establish operation, not a measured quality improvement. The scripted `/ask` behavior remains unchanged. Day 7 (grounded generation, citations, and safeguards) is next.

## Day 7 — cited local answering and prototype boundaries

Connected local hybrid retrieval to `/ask` in opt-in `local` mode. Default answers are explicitly labeled verbatim excerpts, with structured citations and quotes. Optional Ollama synthesis requests structured claims and rejects invalid citation IDs or nonverbatim support quotes. Guards precede retrieval; no evidence and invalid output fail closed. Rules are incomplete and quote validation is not semantic entailment.

Verification: 52 offline tests pass, including citation integrity, missing evidence, guard ordering, and injected model behavior. A real local excerpt smoke test uses the indexed articles. Ollama model synthesis remains unverified without a configured local model. This distinction is visible in the interface and documentation.

## Day 8 — inspectable evidence interface

Added clickable citation markers that open evidence cards, source titles/publishers/section names, exact support quotations, full passages, original-source links, and answer timing. Users choose source excerpts or optional Ollama synthesis, with explicit labels. All content is rendered as text; source URLs are restricted to HTTP(S). Loading, timeout, and server errors restore the form for retry.

Verification: JavaScript syntax check and all 52 backend tests pass. Browser testing submitted a real question, displayed cited source excerpts, and opened the corresponding evidence card through a citation link. The full answer text remains a retrieval-quality target for evaluation; showing a citation does not certify relevance. Responsive styles are included; no formal accessibility audit is claimed.
