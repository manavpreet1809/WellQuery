from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

def train_eval_classifier_doc_split(
    clf,
    pdf: pd.DataFrame,
    test_size: float = 0.15,
    random_seed: int = 42,
) -> Tuple[Any, Dict[str, Any]]:

    rng = np.random.RandomState(random_seed)

    # pdf must have: doc_id, train_text, label
    df = pdf[["doc_id", "train_text", "label"]].copy()

    # build doc_id lists per class
    doc_by_label = (
        df.groupby("label")["doc_id"]
          .unique()
          .to_dict()
    )

    train_docs = set()
    test_docs = set()

    for lab, docs in doc_by_label.items():
        docs = np.array(list(docs))
        rng.shuffle(docs)
        n_test = max(1, int(len(docs) * test_size))
        test_set = set(docs[:n_test])
        train_set = set(docs[n_test:])
        test_docs |= test_set
        train_docs |= train_set

    train_df = df[df["doc_id"].isin(train_docs)]
    test_df = df[df["doc_id"].isin(test_docs)]

    X_train = train_df["train_text"].astype(str).tolist()
    y_train = train_df["label"].astype(str).tolist()
    X_test = test_df["train_text"].astype(str).tolist()
    y_test = test_df["label"].astype(str).tolist()

    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)
    classes = list(clf.named_steps["logreg"].classes_)

    metrics: Dict[str, Any] = {
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "train_docs": int(len(train_docs)),
        "test_docs": int(len(test_docs)),
        "classes": classes,
        "report_text": classification_report(y_test, y_pred, digits=4),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=classes).tolist(),
    }

    if "drug" in classes:
        drug_idx = classes.index("drug")
        y_bin = [1 if yy == "drug" else 0 for yy in y_test]
        metrics["roc_auc_drug"] = float(roc_auc_score(y_bin, y_proba[:, drug_idx]))

    return clf, metrics
