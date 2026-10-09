from typing import Dict, Any, Optional
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

# ensure mlflow experiment exists and set as active
def ensure_experiment(exp_name: str) -> str:
    client = MlflowClient()
    exp = client.get_experiment_by_name(exp_name)

    if exp is None:
        exp_id = client.create_experiment(exp_name)
    else:
        exp_id = exp.experiment_id

    mlflow.set_experiment(experiment_id=exp_id)
    return exp_id

def log_classifier_run(clf, params: Dict[str, Any], metrics: Dict[str, Any], exp_name: str, run_name: str = "question_router_logreg", artifact_path: str = "model") -> Dict[str, str]:
    ensure_experiment(exp_name) # ensure experiment exists

    # start mlflow run
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(params) # log params

        # log metrics
        for k in ["train_rows", "test_rows", "roc_auc_drug"]:
            if k in metrics:
                mlflow.log_metric(k, float(metrics[k]))

        # log readable evaulation outputs
        mlflow.log_text(metrics.get("report_text", ""), "classification_report.txt")
        mlflow.log_dict(
            {
                "classes": metrics.get("classes", []),
                "confusion_matrix": metrics.get("confusion_matrix", []),
            },
            "eval_summary.json",
        )

        mlflow.sklearn.log_model(clf, artifact_path=artifact_path) # log model

        # return identifiers
        run_id = run.info.run_id
        model_uri = f"runs:/{run_id}/{artifact_path}"
        return {"run_id": run_id, "model_uri": model_uri}