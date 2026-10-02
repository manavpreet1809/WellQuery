import os
from dotenv import load_dotenv

load_dotenv()

def _require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

class Settings:
    # Databricks
    DATABRICKS_HOST = _require("DATABRICKS_HOST").rstrip("/")
    DATABRICKS_TOKEN = _require("DATABRICKS_TOKEN")
    CLASSIFIER_ENDPOINT = _require("CLASSIFIER_ENDPOINT")
    RETRIEVER_ENDPOINT = _require("RETRIEVER_ENDPOINT")

    # Routing defaults
    CLASSIFIER_THRESHOLD = float(os.getenv("CLASSIFIER_THRESHOLD", "0.80"))

    # Retrieval defaults
    TOP_K = int(os.getenv("TOP_K", "5"))
    POOL_K = int(os.getenv("POOL_K", "50"))
    MAX_DIST = float(os.getenv("MAX_DIST", "0.85"))

    # LLM
    MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.2-1B-Instruct")
    HF_TOKEN = os.getenv("HF_TOKEN")
    MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "256"))

settings = Settings()
