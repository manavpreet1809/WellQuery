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

## Day 9 — evaluation tooling and draft run (human review pending)

Added 60 explicitly unverified draft questions, grouped paraphrases, split-leakage checks, and a verified-only default. The runner compares four configurations with section-level Recall@5 and MRR@5, records latency, checks excerpt/refusal behavior and rule routes, and exports evidence for human claim review. Source/code/model/dataset provenance accompanies results. Exact-quote validity is not labeled answer correctness.

Verification: 56 tests pass. A complete 60-question draft run produced JSON summaries, retrieval CSV, and answer-review JSONL. Verified-only execution correctly refuses because no questions have been reviewed by the user. The draft test split exposed lower recall with routing (13/14) than unrestricted hybrid (14/14); no quality improvement is claimed and no ranking change was made from this result. See evaluation/README.md for limitations. Human verification of questions and answers is outstanding, so the verified-evaluation acceptance goal is not complete.

## Final delivery, part 1 — results dashboard

Added a read-only `/evaluation` dashboard with run selection, split/configuration comparison, Recall@5 bars, MRR@5, latency, behavior counts, and provenance. Verification labels are derived from counts rather than trusting a summary's label. Missing/invalid summaries are handled explicitly; answers and question text are not exposed through this page.

Verification: 60 tests pass. Browser verification displayed the real draft run, including 0/60 verified questions and the routing regression, and confirmed run selection. The dashboard reports development evidence, not clinically validated accuracy.

## Final delivery, part 2 — human review workflow

Added review-packet export with source evidence, explicit approve/reject decisions, reviewer notes, dataset fingerprints, and application to a new output file. Added answer-review summaries that separate coverage, support, relevance, and uncertain judgments. Export is read-only; no project questions have been automatically verified.

Verification: 67 tests pass, including stale-packet rejection, incomplete decisions, original-file preservation, exclusive output creation, and zero-review reporting. Exported a local packet for all 60 questions with every decision blank. Real human verification remains outstanding.

## Final delivery, part 3 — reproducible demo package

Added a pinned snapshot of the tested demo/test dependencies, setup/ingest/index/evaluate/local commands, a read-only doctor command, and an opt-in real-model smoke check. Rewrote the README around the current implementation, added architecture tradeoffs, a two-minute demo script, a dashboard screenshot, and an explicit completion checklist.

Verification: the dependency snapshot installed into a separate temporary Python 3.12 environment. All 70 tests and the real 38-chunk cited-excerpt smoke check passed there. JavaScript syntax and Git whitespace checks passed. One upstream Starlette/AnyIO deprecation warning remains. This validates the local excerpt demo on macOS Apple Silicon, not live Ollama/Databricks inference or clinical correctness. Human review, corpus expansion, and a recorded presentation remain outstanding.

## Follow-up 1 — expand the source corpus

Expanded from 3 to 15 attributed NIDDK articles, adding kidney health and two medication-information pages alongside diabetes. Rechecked publisher terms and article identity; excluded media. A navigation-only gestational page was replaced with its linked article after the extractor correctly refused it.

Live validation: 15 sources ingested into 201 chunks; repeat ingestion changed 0 documents. The vector index was rebuilt for the expanded corpus. Earlier evaluation results remain historical and must not be presented as metrics for the new corpus. This meets the source-count target, not a claim of comprehensive topic coverage.
