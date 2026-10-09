"""Configuration loaded without requiring remote credentials at startup."""
import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

@dataclass
class Settings:
    BACKEND_MODE: str = field(default_factory=lambda: os.getenv("BACKEND_MODE", "databricks"))
    DATABRICKS_HOST: str = field(default_factory=lambda: os.getenv("DATABRICKS_HOST", "").rstrip("/"))
    DATABRICKS_TOKEN: str = field(default_factory=lambda: os.getenv("DATABRICKS_TOKEN", ""), repr=False)
    CLASSIFIER_ENDPOINT: str = field(default_factory=lambda: os.getenv("CLASSIFIER_ENDPOINT", ""))
    RETRIEVER_ENDPOINT: str = field(default_factory=lambda: os.getenv("RETRIEVER_ENDPOINT", ""))
    CLASSIFIER_THRESHOLD: float = field(default_factory=lambda: float(os.getenv("CLASSIFIER_THRESHOLD", "0.60")))
    TOP_K: int = field(default_factory=lambda: int(os.getenv("TOP_K", "5")))
    POOL_K: int = field(default_factory=lambda: int(os.getenv("POOL_K", "50")))
    MAX_DIST: float = field(default_factory=lambda: float(os.getenv("MAX_DIST", "0.85")))
    MODEL_NAME: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "meta-llama/Llama-3.2-1B-Instruct"))
    HF_TOKEN: str | None = field(default_factory=lambda: os.getenv("HF_TOKEN"), repr=False)
    MAX_NEW_TOKENS: int = field(default_factory=lambda: int(os.getenv("MAX_NEW_TOKENS", "256")))

    def validate_remote(self) -> None:
        """Require credentials only when using remote inference."""
        missing = [name for name in ("DATABRICKS_HOST", "DATABRICKS_TOKEN", "CLASSIFIER_ENDPOINT", "RETRIEVER_ENDPOINT") if not getattr(self, name)]
        if missing:
            raise RuntimeError("Remote backend is not configured")
        if not self.DATABRICKS_HOST.startswith("https://"):
            raise RuntimeError("Databricks requires an HTTPS URL")

settings = Settings()
