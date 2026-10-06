# WellQuery

A third-year university project exploring evidence-based answers to general health-information questions using document retrieval, question routing, and an LLM.

WellQuery builds on Manavpreet Singh's existing MediBot project, adding hybrid retrieval, citations, an evidence panel, and comparative evaluation.

The project is hosted in the [WellQuery repository](https://github.com/manavpreet1809/WellQuery). Its scope is not limited to Canadian public-health sources.

## Planned features

- Keyword, vector, and hybrid document search.
- Medication and condition question routing.
- Answers with passage-level citations and expandable evidence.
- Insufficient-evidence responses and basic prototype safety boundaries.
- A dashboard comparing retrieval quality, answer support, routing accuracy, and latency.

## Status

The original MediBot baseline is imported and an offline scripted chat demo is available. Local retrieval, cited excerpt answers, prototype safeguards, an evidence panel, and a draft evaluation runner are implemented. Live model synthesis and human-verified evaluation remain outstanding. See [project scope and stages](PROJECT_SCOPE.md) and [provenance and reuse status](ATTRIBUTION.md).

The first release targets a local demo using a small permitted document collection and fictional evaluation inputs. Setup instructions and measured results will be added as implementation progresses.

Independent student project; not affiliated with a health authority. General information only, not medical advice. Prototype safeguards are not clinically validated.

## Run locally (Python 3.12)

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
cp .env.example .env
make run
```

Open http://127.0.0.1:8000 and ask **What is WellQuery?** The default `BACKEND_MODE=demo` is a scripted UI demonstration, not medical retrieval or LLM generation. Other questions receive an insufficient-evidence response.

For the original remote flow, set `BACKEND_MODE=databricks`, configure the endpoint variables in `.env`, and install `requirements-llm.txt`. This requires your own Databricks deployments and access to the configured Hugging Face model; the model downloads on first generation. Endpoint responses must contain full `chunk_text`, not previews. No live remote inference has been verified in this repository.

Run `make check` for offline API tests and whitespace checks. Tests use injected services and never download a model or send questions to Databricks.

## Document ingestion

A three-article NIDDK starter catalogue and local SQLite ingestion pipeline are available. Install the updated requirements and run:

```sh
.venv/bin/python -m app.ingest --download
```

See [source permissions, cache behavior, and limitations](data/README.md). The initial run produced **38 chunks**; an unchanged rerun made zero document updates. These are ingestion checks, not retrieval or answer-quality results. The document store now supports cited answers when BACKEND_MODE=local.

See [commit progress](docs/PROGRESS.md) for completed work and remaining validation.

## Local search

Keyword search uses BM25 and works with the web requirements alone:

```sh
.venv/bin/python -m app.search "diabetes symptoms" --mode keyword
```

For semantic search, install the optional embedding dependencies and explicitly download/index the pinned MiniLM model:

```sh
uv pip install --python .venv/bin/python -r requirements-search.txt
.venv/bin/python -m app.search --index --download-model
.venv/bin/python -m app.search "high blood sugar" --mode vector
```

Model files stay in ignored `data/models/`. Searches load the model locally and do not download it automatically. Rebuild the index after ingestion changes. Scores are relevance signals, not probabilities of truth or medical confidence. This is passage retrieval; `/ask` defaults to a scripted demo; set BACKEND_MODE=local for evidence-backed excerpts or explicitly selected Ollama synthesis.

## Hybrid search and routing

```sh
.venv/bin/python -m app.search "diabetes symptoms" --mode hybrid --routing
```

With the server running, use `/docs` to try `GET /search?q=diabetes%20symptoms&mode=hybrid&routing=true`. Modes are `keyword`, `vector`, and `hybrid`; omit routing to compare against unrestricted retrieval. Each result includes source metadata, the full passage, its score, and component ranks. Hybrid retrieval combines up to 50 candidates from each method with reciprocal rank fusion (constant 60).

Local routing is a transparent **rule-based baseline**, not the original trained Databricks classifier. It routes unambiguous medication/condition cues, leaves mixed or unknown questions unrestricted, and reports missing category coverage explicitly. The present condition-only corpus has no medication documents. Routing does not establish whether a question is safe or in scope, and vector results are not evidence that a question is answerable. Local answer citation validation is now available; it does not establish semantic entailment.

Semantic retrieval uses the model's default sequence-length limit; unusually long passages may be truncated during embedding. Keyword search uses the full passage. This limitation should be evaluated before expanding the corpus. Dense retrieval scans the small index exactly; it is not intended for a production-scale collection.

## Cited local answers (Day 7)

Set `BACKEND_MODE=local` in `.env` and restart the server after building the vector index. `/ask` now retrieves evidence and returns numbered citations, exact support quotes, refusal reasons, and timing. Its default `answer_style=excerpts` selects verbatim source sentences; it is **not LLM synthesis**. Existing `demo` and `databricks` modes remain available.

Optional synthesis uses a locally running [Ollama chat API](https://docs.ollama.com/api/chat). Set `OLLAMA_MODEL` to a model you have installed, then request `answer_style=ollama`. Generated claims must cite retrieved chunk IDs and include exact support quotes. This checks citation existence and quotation accuracy, **not whether every claim logically follows from the quotation**. Do not report that validation as factual accuracy. The Ollama adapter is tested with injected responses; live model synthesis requires your local service and has not been verified.

Phrase-based emergency/personal-advice/injection checks run before retrieval in local mode. Dosing patterns, malformed citations, and fabricated quotes block output. These incomplete rules can miss paraphrases or misread negation; they are not clinical triage, a privacy filter, or a complete prompt-injection defense. Legacy Databricks mode does not use these new local safeguards. No questions or answers are persisted by the local pipeline.

In local mode, click a numbered citation to expand its source card. Cards show publisher, section, support quotes, the full passage, and an original-source link. The answer-style selector distinguishes verbatim excerpts from optional AI synthesis; errors keep your question available for retry.

## Evaluate and review (Day 9)

Run `.venv/bin/python -m evaluation.run --include-drafts` to compare four search configurations and export excerpt answers for review. The 60-question set is entirely **unverified**. The default command omits drafts and currently refuses to run without reviewed questions. See [evaluation definitions, results limitations, and review instructions](evaluation/README.md). No verified accuracy or clinical-safety claim is made.

The [local results dashboard](http://127.0.0.1:8000/evaluation) displays saved evaluation runs, comparison tables, recall bars, response-behaviour counts, and provenance. It labels unverified runs as drafts. A fresh checkout needs an evaluation run before results appear.
