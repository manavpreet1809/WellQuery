# Current status

The requested original MediBot architecture is restored as the WellQuery default:

- FastAPI request/response interface.
- Databricks classifier and retriever endpoints with original serving payloads.
- Original Transformers wrapper, LLaMA-3.2-1B-Instruct model, and system prompt.
- Imported original Spark/Delta ingestion, TF-IDF training, MLflow registration, and deployment notebooks.
- Enhancements: validation, sanitized failures, evidence display, diagnostics, and offline integration tests.

Live endpoint and LLaMA inference remain unverified because this workspace has no Databricks credentials configured. Model access and the Databricks workspace must be configured before a live demo. No cloud resources were created and no claim of public deployment is made.

The prior SQLite/MiniLM/Ollama experiment remains opt-in. Its 15-document corpus, 92 draft questions, saved results, screenshots, and October 7 report are historical local-experiment evidence. They do not validate the default Databricks/LLaMA product.

## Latest verification

- 117 offline tests pass; whitespace checks pass.
- Installed default runtime: Transformers 4.47.1, PyTorch 2.7.1, Accelerate 1.2.1; imports and dependency compatibility checked.
- Original system prompt preserved; model loading serialized for concurrent first requests.
- Default and optional experiment environments separated (`.venv` and `.venv-local`).
- Live readiness probe stops before network/model calls because endpoint configuration is missing.

To finish live verification, fill `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `CLASSIFIER_ENDPOINT`, `RETRIEVER_ENDPOINT`, and model access (`HF_TOKEN` or authenticated Hugging Face login) in the untracked local configuration. Run `make smoke`, restart `make run`, and verify a supported question in the browser. A successful smoke test confirms integration only, not clinical accuracy.
