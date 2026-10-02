"""WellQuery HTTP API; demo mode works without accounts or model downloads."""
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator, model_validator
from app.config import settings
from app.rag import NO_EVIDENCE, answer_question

ROOT = Path(__file__).resolve().parents[1]

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    threshold: float = Field(default=0.8, ge=0, le=1, allow_inf_nan=False)
    top_k: int = Field(default=5, ge=1, le=20)
    pool_k: int = Field(default=50, ge=1, le=100)
    max_dist: float = Field(default=0.85, ge=0, le=2, allow_inf_nan=False)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        """Reject whitespace-only input."""
        if not value.strip():
            raise ValueError("Question cannot be empty")
        return value.strip()

    @model_validator(mode="after")
    def check_pool(self):
        """Do not request more final results than candidates."""
        if self.top_k > self.pool_k:
            raise ValueError("pool_k must be at least top_k")
        return self

class AskResponse(BaseModel):
    question: str
    route: str
    confidence: float
    answer: str
    chunks_used: int
    chunks: list[dict]
    refused: bool
    mode: Literal["demo", "databricks"]

def create_app(mode: str | None = None, client=None, generate=None, search_database=None, search_embed=None) -> FastAPI:
    """Construct the app with injectable dependencies for offline tests."""
    backend = mode or settings.BACKEND_MODE
    if backend not in {"demo", "databricks"}:
        raise ValueError("BACKEND_MODE must be demo or databricks")
    application = FastAPI(title="WellQuery", version="0.2.0")
    application.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    templates = Jinja2Templates(directory=ROOT / "templates")

    @application.get("/", response_class=HTMLResponse)
    @application.get("/ui", response_class=HTMLResponse)
    def ui(request: Request):
        return templates.TemplateResponse(request=request, name="index.html", context={"mode": backend})

    @application.get("/health")
    def health():
        return {"status": "ok", "mode": backend, "remote_inference_verified": False}

    @application.get("/search")
    def search_endpoint(q: str = Query(min_length=1, max_length=1000),
                        mode: Literal["keyword", "vector", "hybrid"] = "hybrid",
                        k: int = Query(default=5, ge=1, le=20), routing: bool = False):
        """Return source passages, not generated medical answers."""
        from app.search import DATABASE, search_report
        import sqlite3
        try:
            return search_report(q, mode, k, database=search_database or DATABASE,
                                 embed=search_embed, routing=routing)
        except ValueError:
            raise HTTPException(422, "Invalid search input or vector data.") from None
        except (RuntimeError, ImportError, OSError, sqlite3.Error):
            raise HTTPException(503, "Search unavailable. Ingest documents and build the vector index for vector/hybrid mode.") from None

    @application.post("/ask", response_model=AskResponse)
    def ask(req: AskRequest):
        if backend == "demo":
            supported = req.question.lower().rstrip("?!. ") in {"what is wellquery", "what does wellquery do"}
            return dict(question=req.question, route="all", confidence=0,
                        answer=("WellQuery is a student project for answering questions from documents. "
                                "This is a scripted interface demo; health retrieval and AI generation are not active.")
                               if supported else "Demo mode only answers ‘What is WellQuery?’. " + NO_EVIDENCE,
                        chunks_used=0, chunks=[], refused=not supported, mode=backend)
        try:
            active_client = client
            if active_client is None:
                from app.databricks_client import DatabricksClient
                active_client = DatabricksClient()
            active_generator = generate
            if active_generator is None:
                from llm.llm import answer_with_llm
                active_generator = answer_with_llm
            result = answer_question(req.question, active_client, active_generator,
                                     threshold=req.threshold, top_k=req.top_k,
                                     pool_k=req.pool_k, max_dist=req.max_dist)
            return {**result, "mode": backend}
        except RuntimeError:
            raise HTTPException(503, "Backend unavailable. Check the server configuration.") from None
        except Exception:
            raise HTTPException(502, "The answer service could not complete this request. Please try again.") from None

    return application

app = create_app()
