from typing import List, Dict, Tuple
import os
import json
import tempfile
import joblib
import mlflow

def log_retriever_artifacts(
    vectorizer,
    knn,
    chunk_ids: List[str],
    metadata: Dict,
    params: Dict,
    run_name: str = "tfidf_knn_retriever",
    artifact_path: str = "retriever",
) -> str:
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(params)

        with tempfile.TemporaryDirectory() as td:
            vec_path = os.path.join(td, "vectorizer.joblib")
            knn_path = os.path.join(td, "knn.joblib")
            ids_path = os.path.join(td, "chunk_ids.json")
            meta_path = os.path.join(td, "metadata.json")

            joblib.dump(vectorizer, vec_path)
            joblib.dump(knn, knn_path)

            with open(ids_path, "w") as f:
                json.dump(chunk_ids, f)

            with open(meta_path, "w") as f:
                json.dump(metadata, f)

            mlflow.log_artifact(vec_path, artifact_path=artifact_path)
            mlflow.log_artifact(knn_path, artifact_path=artifact_path)
            mlflow.log_artifact(ids_path, artifact_path=artifact_path)
            mlflow.log_artifact(meta_path, artifact_path=artifact_path)

        return run.info.run_id

def load_retriever_artifacts(run_id: str, artifact_path: str = "retriever"):
    local_dir = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path=artifact_path)
    vectorizer = joblib.load(os.path.join(local_dir, "vectorizer.joblib"))
    knn = joblib.load(os.path.join(local_dir, "knn.joblib"))

    with open(os.path.join(local_dir, "chunk_ids.json"), "r") as f:
        chunk_ids = json.load(f)

    with open(os.path.join(local_dir, "metadata.json"), "r") as f:
        metadata = json.load(f)

    return vectorizer, knn, chunk_ids, metadata
