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

The original MediBot baseline is imported and an offline scripted chat demo is available. Retrieval improvements, clinical safeguards, and evaluation are still in development. See [project scope and stages](PROJECT_SCOPE.md) and [provenance and reuse status](ATTRIBUTION.md).

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

See [source permissions, cache behavior, and limitations](data/README.md). The initial run produced **38 chunks**; an unchanged rerun made zero document updates. These are ingestion checks, not retrieval or answer-quality results. The document store is not yet connected to the chat endpoint.

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

Model files stay in ignored `data/models/`. Searches load the model locally and do not download it automatically. Rebuild the index after ingestion changes. Scores are relevance signals, not probabilities of truth or medical confidence. This is passage retrieval; `/ask` remains the scripted demo unless configured for the original remote backend.
