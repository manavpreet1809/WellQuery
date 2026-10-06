# Two-minute classroom demo

## Before presenting

From the repository root run `make setup`, `make ingest`, `make index`, `make check`, `make smoke`, and `make evaluate`, then start `make local`. The first three steps may download files. Repeated setup is unnecessary if your environment is ready. Run a sample question once to warm the model before timing the demo.

## Script

| Time | Action | Explanation |
|---|---|---|
| 0:00–0:20 | Open the chat and show the source-excerpt selection | “WellQuery extends my earlier MediBot project. This mode retrieves source text; it does not generate new medical advice.” |
| 0:20–0:50 | Ask “What are the symptoms of type 2 diabetes?” and open a citation | Show the publisher, section, exact quotation, and original-source link. A citation establishes provenance, not completeness or clinical correctness. |
| 0:50–1:10 | Ask “How do I repair a bicycle?” | Show insufficient evidence. Then use a fictional emergency phrase such as “I cannot breathe” to demonstrate the fixed redirect. Explain that phrase coverage is limited. |
| 1:10–1:40 | Open Evaluation results | Compare keyword, vector, hybrid, and routed hybrid. Point out the draft label, 0/60 verified questions, and the routing regression rather than claiming a guaranteed improvement. |
| 1:40–2:00 | Show the architecture and status checklist | Explain tests, human review needs, limited source coverage, and optional synthesis that still needs live validation. |

Do not demonstrate personalized diagnosis or medication changes as supported functionality. Do not present draft metrics as validated accuracy. Record your own demo video only after checking the outputs you plan to show.

## Troubleshooting

- **No database:** run `make ingest`. Network/source errors leave clear CLI messages; a changed publisher URL/selector needs catalogue review.
- **Missing or stale vector index:** run `make index` after ingestion. The first run downloads the embedding model.
- **No model files:** rerun index setup with network access. `make doctor` checks the index; `make smoke` additionally loads the cached model.
- **Empty dashboard:** run `make evaluate` once. Each run saves separate files under `evaluation/results/`.
- **Scripted answers:** use `make local`; `make run` respects your environment and defaults to demo mode.
- **Ollama unavailable:** use source excerpts. AI synthesis requires a separately installed local model and `OLLAMA_MODEL`; it is not part of the verified demo path.
- **Port 8000 occupied:** stop your existing server or run `BACKEND_MODE=local .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001` and open that port.
- **Verified evaluation refuses to run:** this is expected until you review questions. Follow `evaluation/README.md`; do not bulk-mark them verified to bypass the check.

Tested setup: macOS Apple Silicon, Python 3.12. Other operating systems, cold-machine network access, and legacy Databricks dependencies have not been validated.
