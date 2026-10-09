# Original MediBot Databricks pipeline

Imported from the supplied MediBot-main folder. Source-file SHA-256 hashes before changes are in `docs/medibot-databricks-baseline.json`. Workspace-specific personal paths were replaced with portable bootstrap discovery and `/Shared` experiment paths. Notebook outputs are cleared. A missing SQL statement terminator in the registry setup was fixed. Training algorithms, data sources, registry/model names, and serving payloads are preserved.

These notebooks require a Databricks workspace with Spark, Delta, MLflow, pandas, scikit-learn, joblib, requests, and the appropriate Unity Catalog/serving permissions. They have not been executed in this workspace. They are not local FastAPI dependencies.

## Setup order

1. Import this directory into your Databricks workspace, preserving `helpers/` alongside `notebooks/`. Run notebooks from `notebooks/`, so `_bootstrap` resolves the helpers directory.
2. Provision the `workspace` catalog, `med` schema and `medibot_bronze` volume, or consistently adapt the original identifiers to your workspace. Review the SQL notebooks under `notebooks/0_tables_setup/` before executing. Cleaning/chunking notebooks overwrite their destination tables.
3. Run `raw_data_ingestion_medlineplus`, then `raw_data_ingestion_openfda`.
4. Run `tranform_clean_docs` (original spelling), then `transform_chunk_docs`.
5. Run `train_question_classifier_logreg` and `train_tfidf_knn`.
6. Run `deploy_classifier_pyfunc` and `deploy_retriever_pyfunc` to package/register the original MLflow models.
7. Create serving endpoints for `workspace.med.medibot_classifier` and `workspace.med.medibot_retriever`. The supplied `update_serving` notebook updates **existing** endpoints; it does not create them.
8. Configure the application `.env` with their names and credentials; run `make smoke` from the application checkout.

The classifier returns `predictions: [{route, confidence, ...}]`. The retriever returns `predictions: [{chunks: [...], ...}]`; each usable chunk must contain full `chunk_text`, not only `chunk_text_preview`. The API preserves the original `dataframe_records` request format.

The original defaults are retained: serving request threshold 0.60, top_k 5, pool_k 50, max_dist 0.85. The original config helper used 0.80 whereas its HTTP request used 0.60; WellQuery defaults to the user-facing request value and allows environment configuration.

Data-source permissions and service availability must be checked when running ingestion. No trained models, downloaded datasets, or credentials are included.
