> Historical local-experiment document. The current default is the restored Databricks/Transformers LLaMA architecture; see [current status](STATUS.md) and the root README. Results below do not validate that default pipeline.

# WellQuery: extending MediBot with inspectable local retrieval

**Author:** Manavpreet Singh · **Release evidence:** October 7, 2026

## Objective and scope

WellQuery extends the author's MediBot project into a reproducible local application for exploring general diabetes, kidney-health, and medication information. The goal is to make retrieval and supporting evidence inspectable and to evaluate failures explicitly. It is an educational software project, not a diagnostic service, treatment recommender, or clinically validated assistant. The current corpus is US NIDDK material; it is not a Canadian-specific health service.

## Original work and enhancement

The supplied MediBot baseline already included FastAPI, a web chat, Databricks classifier/retriever calls, and an LLM prompt with medical-advice restrictions. Those components are acknowledged rather than presented as newly invented. Imported-file hashes are preserved in `medibot-baseline.json`.

| Area | Original supplied MediBot | WellQuery contribution |
|---|---|---|
| Retrieval execution | Remote Databricks dependencies | Reproducible SQLite corpus and local search |
| Search experiments | Existing remote retrieval pipeline | BM25, MiniLM vectors, reciprocal-rank fusion, explicit routing comparison |
| Response evidence | Retrieved chunks and prompted grounding | Citation IDs, exact support quotations, expandable source cards |
| Generation | Original Transformers/Llama wrapper | Local Ollama adapter with structured claims and immutable evidence IDs |
| Request boundaries | Prompt-level instructions | Auditable pre-retrieval rules, scoped negation, output checks, regression tests |
| Evaluation | Original training/evaluation notebooks | Application-level draft datasets, metrics, failure exports, dashboard, review workflow |
| Delivery | Original project setup | Pinned demo dependencies, smoke checks, local commands, CI and report |

The original Databricks deployment was not reproduced. Architectural improvements do not establish that WellQuery has higher medical-answer accuracy.

## Implementation

Fifteen approved catalogue entries are downloaded with robots checks, cache receipts, hashes, size limits, and section-aware extraction. Media and navigation are excluded. The resulting 201 chunks retain publisher, title, URL, section, and source terms. Ingestion is transactional and repeat runs avoid unchanged document writes.

BM25 provides lexical retrieval. A revision-pinned `all-MiniLM-L6-v2` encoder provides normalized vectors; exact cosine scanning is appropriate for this small corpus. Reciprocal-rank fusion combines ranks without treating lexical and cosine scores as comparable. Rule routing is an inspectable experimental baseline, not a trained medical classifier. SQLite keeps setup small at the cost of large-scale throughput.

Source-excerpt mode returns verbatim sentences. It skips sentences disallowed by the conservative output rules instead of rejecting all remaining evidence. Equal-overlap sentences retain retrieval order. Synthesis mode uses Qwen2.5 1.5B through local Ollama: the model selects from short evidence sentences and emits claims with evidence IDs. The server maps IDs to immutable source quotes and validates them. Unknown IDs, incomplete output, invalid envelopes, unsupported quotations, and disallowed output are rejected. This proves attribution structure, not semantic entailment.

Question text is processed locally in the local backend. There is no account system or persistent chat-history feature. The app is bound to localhost; it is not configured for public deployment. External document/model downloads occur during setup. The legacy remote backend remains separate and unverified.

## Evaluation method

The original set contains 60 draft questions. A 20-case challenge set exposed unfamiliar urgent wording, negation, personal-dose requests, injection variants, and unrelated questions sharing health vocabulary. These sets guided development and are therefore regression evidence, not independent accuracy estimates.

After the boundary and excerpt changes, a separate 12-question supplementary set was authored and evaluated once. It has not been used to tune retrieval. It is still AI-authored, small, and unverified, so it is not a substitute for an independently authored, human-labeled test set. All 92 question records retain `verified: false`.

Recall@5 measures whether labeled document sections appear among the first five chunks, deduplicating sections. MRR@5 measures the rank of the first labeled section. Behavior matching checks the expected answer/refusal category. An answer being returned does not mean it is relevant or correct. Human claim-support and relevance fields remain blank. Timings include model loading and are not controlled performance benchmarks.

## Results

| Dataset | Cases | Answer/refusal category matches | Meaning |
|---|---:|---:|---|
| Original draft set | 60 | 60/60 | Regression behavior after fixes |
| Challenge draft set | 20 | 20/20 | Previously observed failures now covered |
| Supplementary draft set | 12 | 12/12 | Small, unverified post-change check |

The earlier challenge run had 6 behavior mismatches. The initial expanded-corpus rerun also found a coding request answered from unrelated medicine text and a lab-value sentence causing whole-answer rejection. Tests now cover these failure mechanisms.

Retrieval is less complete than the behavior counts suggest. On the supplementary set's six factual questions, keyword Recall@5 was 0.50 and vector, hybrid, and routed hybrid were 0.667. The labeled section was missed in two questions even though an answer was returned. On the original draft test subset, unrestricted hybrid achieved Recall@5 1.0 versus 0.929 with routing. Routing is therefore not claimed as a universal improvement. Draft route labels also produce mismatches and need human review.

Machine-readable summaries, per-configuration retrieval rows, and failure events are checked into `docs/results/`. Full local answer-review exports remain under ignored `evaluation/results/`. Source/code/model/dataset hashes accompany evaluation runs; their dirty-tree flag records execution before the release commit.

## Controlled MediBot prompt comparison

`python -m evaluation.compare --output <new-directory>` runs the unchanged, hash-verified MediBot system prompt and WellQuery on the same five questions using the same local model and WellQuery's retrieval context. It isolates prompt/output handling; it does **not** replay MediBot's original classifier, remote retriever, or Llama model.

The final run produced three accepted, cited WellQuery synthesis answers and two pre-generation refusals. All paired outputs are preserved in `docs/results/paired-answers.json` for review. No automatic judge was used to label one answer more correct than the other. An earlier live run failed quotation validation; replacing model-copied quotes with immutable sentence IDs resolved that mechanical failure without relaxing citation validation.

The live model was Qwen2.5 1.5B, digest `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`, served by Ollama 0.40.0 on Apple Silicon. The downloaded runtime matched its published GitHub asset SHA-256. The browser test generated an answer, opened a citation, and displayed the exact source passage.

## Validation and limitations

109 automated tests pass locally, plus the real 201-chunk retrieval smoke check and the live synthesis probe. Tests cover ingestion, stale-index protection, ranking, boundaries, invalid citations, API failures, evaluation leakage checks, review integrity, dashboard parsing, and model transport. GitHub Actions runs the offline unit suite. A screenshot of live synthesis is included in `docs/images/live-synthesis.png`.

Remaining limitations are substantive: rule-based boundaries cannot cover all language; negation handling is intentionally narrow; retrieval misses relevant sections; citations do not prove entailment; a small model may omit or distort facts; source updates may invalidate extraction; and no clinician or independent human review has been recorded. This release completes the local software demonstration, not clinical validation.

## Reproduction and submission

Follow the root README for environment, corpus, index, and server setup. Use `make check`, `make smoke`, `make model-smoke`, and the evaluation commands in `evaluation/README.md`. The corpus, downloaded model/runtime, caches, credentials, and local review packets are excluded from Git.

For submission, the author must check the course's prior-work and AI-assistance requirements, personally review the draft labels and outputs using the supplied packets, and adapt this report to the actual rubric. `docs/DEMO.md` supplies a timed demonstration script. No reviewer identity, instructor approval, or presentation recording has been fabricated.
