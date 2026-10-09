# Demonstrate the default product

1. Follow `Databricks/README.md` to prepare the original serving models/endpoints, or use existing compatible endpoints.
2. Run `make setup`, configure `.env` for Databricks and Hugging Face model access, and run `make doctor`.
3. Run `make smoke` to explicitly verify retrieval and generation. First-time model loading may take time.
4. Run `make run`, open http://127.0.0.1:8000, and ask a general question supported by your Databricks corpus.
5. Inspect the LLaMA answer and expand the retrieved passages. Explain the classifier → retriever → route filter → Transformers flow.

Without credentials, demonstrate the offline tests or explicitly select `BACKEND_MODE=demo make run`; identify it as scripted. Do not present a local Ollama result or old screenshot as a live Databricks/LLaMA result.

`make check` is offline. `make doctor` only checks configuration/packages. `make smoke` makes real service calls and can download model weights; it is not a medical correctness test.
