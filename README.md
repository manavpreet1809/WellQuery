# WellQuery

WellQuery enhances the supplied MediBot project while keeping its original architecture as the default: **FastAPI → Databricks classifier → Databricks retriever → Hugging Face Transformers → LLaMA**.

The default model is `meta-llama/Llama-3.2-1B-Instruct`, running through the original CPU/float32 Transformers wrapper. The original system prompt is preserved. Databricks uses the original TF-IDF/logistic-regression classifier and TF-IDF/nearest-neighbor retriever, with Spark/Delta data processing and MLflow model registration. The original MedlinePlus/openFDA ingestion, training, and serving notebooks are included under [Databricks](Databricks/README.md).

## Run the original pipeline

Requires Python 3.12, `uv`, accessible Databricks serving endpoints, and access to the configured Hugging Face model.

```sh
make setup
# On first setup only: copy .env.example to .env, then fill in your values.
make doctor     # checks configuration and installed dependencies; no remote calls
make run        # http://127.0.0.1:8000
```

Set these values in your untracked `.env`:

```dotenv
BACKEND_MODE=databricks
DATABRICKS_HOST=https://your-workspace.example.com
DATABRICKS_TOKEN=
CLASSIFIER_ENDPOINT=medibot-classifier
RETRIEVER_ENDPOINT=medibot-retriever
MODEL_NAME=meta-llama/Llama-3.2-1B-Instruct
HF_TOKEN=
```

Use your actual endpoint names. Obtain model access through Hugging Face if required; a cached authenticated login can also supply access. The first generation may download model weights. `make smoke` explicitly calls both configured endpoints and loads/generates with LLaMA. It can incur endpoint usage and requires network/model access.

The application can render its UI without credentials, but answers return a service-unavailable error until configured. It never silently falls back to Ollama, Qwen, SQLite retrieval, or scripted answers.

## Enhancements on the original foundation

- Input length/range validation, whitespace handling, and candidate-count checks.
- Validation of serving responses and refusal to generate without full source passages.
- Original category routing and fallback to unfiltered retrieved passages.
- Expandable retrieved evidence next to the LLaMA answer and request timing.
- Sanitized service errors, lazy model loading, configuration diagnostics, and offline contract tests.
- An evaluation dashboard for inspecting saved runs. Existing local experiment results are labeled separately and do not measure the restored Databricks/LLaMA system.

Retrieved passages are inspectable evidence, **not verified sentence-level citations**. The original prompt asks for grounded general information and no personalized treatment; this is a student prototype, not medical advice.

## Verification status

The original architecture is restored in code. Offline tests exercise endpoint payloads, routing, evidence handling, and the Transformers wrapper with substitutes. Live Databricks/LLaMA inference has **not** been verified in this workspace: endpoint credentials are absent. Neither original model accuracy nor deployment success is claimed.

Run `make check` for offline tests and whitespace checks. Read [setup and architecture](docs/ARCHITECTURE.md), [status](docs/STATUS.md), and [provenance](ATTRIBUTION.md).

## Optional local experiments

Earlier SQLite/BM25/MiniLM and Ollama work is retained as an explicitly selected experiment, not the product's default foundation. Run `make setup-local` to install `requirements-demo.lock` in a separate `.venv-local` environment; then use `make ingest`, `make index`, `make local-smoke`, and `make local`. These experiments have their own corpus and draft evaluation results. Do not use those results as evidence of Databricks or LLaMA performance.

`BACKEND_MODE=demo make run` starts the scripted UI-only demonstration. `make evaluate`, `make compare`, and the saved [historical report](docs/REPORT.md) concern the local experiment, not a live comparison against the original deployment.
