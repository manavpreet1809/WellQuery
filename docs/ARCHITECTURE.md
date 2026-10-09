# WellQuery architecture

## Default product: original MediBot foundation

```text
Browser → FastAPI /ask
              → Databricks classifier (TF-IDF + logistic regression)
              → Databricks retriever (TF-IDF + nearest neighbors)
              → category filter, original fallback
              → original prompt + Transformers LLaMA-3.2-1B-Instruct
              → answer and inspectable retrieved passages
```

Databricks notebooks ingest MedlinePlus/openFDA, clean and chunk documents into Delta tables, train both models, register MLflow artifacts, and package serving models. Their original code is in `Databricks/`; workspace setup is documented there.

`app/config.py` defaults to `databricks`. `app/databricks_client.py` preserves the original endpoint payloads. `app/rag.py` adds response validation and evidence metadata around the original orchestration. `llm/llm.py` preserves the original CPU/float32 generation settings, tokenizer chat template, and model identifier; imports/model loading are lazy. `llm/prompt.py` is the original prompt.

Input validation, sanitized errors, empty-evidence handling, tests, and evidence display enhance this pipeline without changing its classifier, retriever, or generator. An unavailable remote service fails visibly; there is no automatic local fallback. Retrieved passages are not proof of sentence-level entailment.

## Explicit experiments

`BACKEND_MODE=local` uses the prior SQLite, BM25/MiniLM, optional Ollama experiment. `BACKEND_MODE=demo` is scripted. Neither is selected by the default product configuration. The local phrase guards, immutable evidence-ID synthesis, and draft evaluations belong to that separate experimental path and are not claimed as features of the original LLaMA generation path.

## Verification boundary

Offline contract tests use fake endpoint responses and a fake Transformers model pipeline. They do not establish cloud availability, model access, model accuracy, or clinical quality. Use `make doctor` for configuration diagnostics and `make smoke` for an explicit live integration probe once credentials and model access are configured.
