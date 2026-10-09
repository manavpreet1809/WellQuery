# Original MediBot Databricks pipeline

Imported from the supplied MediBot-main folder. Source-file SHA-256 hashes before changes are in `docs/medibot-databricks-baseline.json`. Workspace-specific personal paths were replaced with portable bootstrap discovery and `/Shared` experiment paths. Notebook outputs are cleared. A missing SQL statement terminator in the registry setup was fixed. Later fixes: `test_retrieval` now runs the bootstrap, deploy notebooks register explicit Unity Catalog names and pin serving requirements, and setup/endpoint-creation notebooks were added. Training algorithms, data sources, registry/model names, and serving payloads are preserved.

These notebooks require a Databricks workspace with Spark, Delta, MLflow, pandas, scikit-learn, joblib, requests, and the appropriate Unity Catalog/serving permissions. They have not been executed in this workspace. They are not local FastAPI dependencies.

## Setup order

1. Import this directory into your Databricks workspace, preserving `helpers/` alongside `notebooks/`. Run notebooks from `notebooks/`, so `_bootstrap` resolves the helpers directory.
2. Run `0_tables_setup/create_schema_and_volume` first. It creates the `med` schema and `medibot_bronze` volume in the `workspace` catalog; the other setup notebooks and the ingestion notebooks assume both exist. If your workspace has no `workspace` catalog, adapt the identifiers consistently. Then run the remaining `0_tables_setup` notebooks. Cleaning/chunking notebooks overwrite their destination tables.
3. Run `raw_data_ingestion_medlineplus`, then `raw_data_ingestion_openfda`. These download from medlineplus.gov and api.fda.gov; workspaces with restricted outbound internet (including Free Edition) may block them.
4. Run `tranform_clean_docs` (original spelling), then `transform_chunk_docs`.
5. Run `train_question_classifier_logreg` and `train_tfidf_knn`. Optionally run `test_retrieval` to inspect retrieval before deploying.
6. Run `deploy_classifier_pyfunc` and `deploy_retriever_pyfunc`. They register `workspace.med.medibot_classifier` and `workspace.med.medibot_retriever` in Unity Catalog, with serving requirements pinned to the notebook runtime's library versions.
7. Run `create_serving_endpoints` once. It creates the `medibot-classifier` and `medibot-retriever` CPU endpoints (Small, scale-to-zero) and waits until they are ready; the first build can take 20+ minutes. **Endpoints are billed while running.** After later retraining, run `update_serving` to move existing endpoints to the newest versions.
8. Configure the application `.env` with the endpoint names and credentials; run `make doctor`, then `make smoke` from the application checkout.

A scaled-to-zero endpoint can take several minutes to start after being idle, so the first request after a pause may time out. `make smoke` reports this case; retry after a few minutes.

The classifier returns `predictions: [{route, confidence, ...}]`. The retriever returns `predictions: [{chunks: [...], ...}]`; each usable chunk must contain full `chunk_text`, not only `chunk_text_preview`. The API preserves the original `dataframe_records` request format.

The original defaults are retained: serving request threshold 0.60, top_k 5, pool_k 50, max_dist 0.85. The original config helper used 0.80 whereas its HTTP request used 0.60; WellQuery defaults to the user-facing request value and allows environment configuration.

Data-source permissions and service availability must be checked when running ingestion. No trained models, downloaded datasets, or credentials are included.
