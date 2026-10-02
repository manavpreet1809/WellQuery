import requests
from app.config import settings

class DatabricksClient:
    def __init__(self):
        self.host = settings.DATABRICKS_HOST  # base host
        self.token = settings.DATABRICKS_TOKEN  # auth token
        self.classifier = settings.CLASSIFIER_ENDPOINT  # classifier endpoint name
        self.retriever = settings.RETRIEVER_ENDPOINT  # retriever endpoint name
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }  # request headers

    def _invoke(self, endpoint: str, record: dict) -> dict:
        url = f"{self.host}/serving-endpoints/{endpoint}/invocations"  # serving url
        payload = {"dataframe_records": [record]}  # single row
        response = requests.post(url, headers=self.headers, json=payload, timeout=60)  # call endpoint
        response.raise_for_status()  # raise on http error
        
        return response.json()

    def classify(self, question: str, threshold: float | None = None) -> dict:
        t = settings.CLASSIFIER_THRESHOLD if threshold is None else float(threshold)  # pick threshold
        
        return self._invoke(self.classifier, {"question": question, "threshold": t})
    
    def retrieve(self, question: str, top_k: int | None = None, pool_k: int | None = None, max_dist: float | None = None) -> dict:
        tk = settings.TOP_K if top_k is None else int(top_k)  # pick top_k
        pk = settings.POOL_K if pool_k is None else int(pool_k)  # pick pool_k
        md = settings.MAX_DIST if max_dist is None else float(max_dist)  # pick max_dist
        
        return self._invoke(
            self.retriever,
            {"question": question, "top_k": tk, "pool_k": pk, "max_dist": md},
        )