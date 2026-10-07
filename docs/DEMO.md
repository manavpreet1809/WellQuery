# Two-minute classroom demo

## Before presenting

From the repository root run `make setup`, `make ingest`, `make index`, `make check`, `make smoke`, and `make evaluate`, then start `make local`. The first three steps may download files. Repeated setup is unnecessary if your environment is ready. Run a sample question once to warm the model before timing the demo.

## Script

| Time | Action | Explanation |
|---|---|---|
| 0:00–0:20 | Open the chat and show the source-excerpt selection | “WellQuery extends my earlier MediBot project. This mode retrieves source text; it does not generate new medical advice.” |
| 0:20–0:50 | Ask “What are the symptoms of type 2 diabetes?” and open a citation | Show the publisher, section, exact quotation, and original-source link. A citation establishes provenance, not completeness or clinical correctness. |
| 0:50–1:10 | Ask “How do I repair a bicycle?” | Show insufficient evidence. Then use a fictional emergency phrase such as “I cannot breathe” to demonstrate the fixed redirect. Explain that phrase coverage is limited. |
| 1:10–1:40 | Open Evaluation results | Compare keyword, vector, hybrid, and routed hybrid. Point out the draft label, the unverified questions, and the routing regression rather than claiming a guaranteed improvement. |
| 1:40–2:00 | Show the architecture and status checklist | Explain tests, human review needs, limited source coverage, and live-tested synthesis and the distinction between structural citation checks and human quality review. |

Do not demonstrate personalized diagnosis or medication changes as supported functionality. Do not present draft metrics as validated accuracy. Record your own demo video only after checking the outputs you plan to show.

## Troubleshooting

- **No database:** run `make ingest`. Network/source errors leave clear CLI messages; a changed publisher URL/selector needs catalogue review.
- **Missing or stale vector index:** run `make index` after ingestion. The first run downloads the embedding model.
- **No model files:** rerun index setup with network access. `make doctor` checks the index; `make smoke` additionally loads the cached model.
- **Empty dashboard:** run `make evaluate` once. Each run saves separate files under `evaluation/results/`.
- **Scripted answers:** use `make local`; `make run` respects your environment and defaults to demo mode.
- **Ollama unavailable:** use source excerpts. Run `make model-serve` in a separate terminal, `make model-pull` once, and set `OLLAMA_MODEL=qwen2.5:1.5b`. `make model-smoke` verifies generation.
- **Port 8000 occupied:** stop your existing server or run `BACKEND_MODE=local .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001` and open that port.
- **Verified evaluation refuses to run:** this is expected until you review questions. Follow `evaluation/README.md`; do not bulk-mark them verified to bypass the check.

Tested setup: macOS Apple Silicon, Python 3.12. Other operating systems, cold-machine network access, and legacy Databricks dependencies have not been validated.


## Optional synthesis segment (one extra minute)

With the local model server running, select AI synthesis and ask “What is type 2 diabetes?”. Open its first citation. Explain that WellQuery maps a model-selected evidence ID to the original quote rather than trusting the model to reproduce it. Show `docs/results/paired-answers.json` and explain why this is a controlled prompt comparison, not a full replay of the original MediBot deployment.

## Presentation outline

1. Problem and supplied MediBot baseline (one slide).
2. Your WellQuery enhancements and architecture (two slides).
3. Live excerpt and synthesis demonstration (two minutes).
4. Retrieval comparisons, failure fixes, and remaining misses (one slide).
5. Limitations, reproducibility, and next steps (one slide).

Use REPORT.md for the written narrative. Review the displayed examples personally before recording; do not state that automated checks prove medical accuracy.
