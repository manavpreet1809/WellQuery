"""Shared MediBot classification/retrieval orchestration."""
from typing import Any
from time import perf_counter

NO_EVIDENCE = "I could not find enough information in the available documents to answer that."

def _first_prediction(response: dict) -> dict:
    """Validate the serving endpoint response before using it."""
    predictions = response.get("predictions")
    if not isinstance(predictions, list) or not predictions or not isinstance(predictions[0], dict):
        raise ValueError("Invalid serving response")
    return predictions[0]

def filter_chunks_by_route(chunks: list[dict], route: str) -> list[dict]:
    """Preserve MediBot's route filter and fallback to all evidence."""
    if route not in {"drug", "condition"}:
        return chunks
    return [c for c in chunks if c.get("category") == route] or chunks

def answer_question(question: str, client: Any, generate: Any, *, threshold: float = 0.8,
                    top_k: int = 5, pool_k: int = 50, max_dist: float = 0.85) -> dict:
    """Use one pipeline for the API and tests; never generate with empty evidence."""
    started = perf_counter()
    classified = _first_prediction(client.classify(question, threshold))
    route = classified.get("route", "all")
    if route not in {"drug", "condition", "all"}:
        route = "all"
    confidence = float(classified.get("confidence", 0))
    if not 0 <= confidence <= 1:
        raise ValueError("Invalid confidence")
    retrieved = _first_prediction(client.retrieve(question, top_k, pool_k, max_dist))
    chunks = retrieved.get("chunks", [])
    if not isinstance(chunks, list) or any(not isinstance(c, dict) for c in chunks):
        raise ValueError("Invalid chunks")
    chunks = [c for c in chunks if isinstance(c.get("chunk_text"), str) and c["chunk_text"].strip()]
    chunks = filter_chunks_by_route(chunks, route)[:top_k]
    answer = generate(question, chunks) if chunks else NO_EVIDENCE
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Empty generated answer")
    # Evidence is shown separately: these are retrieved passages, not verified
    # sentence-level citations for the free-text answer produced by the original prompt.
    citations = [dict(n=i, title=c.get("title") or "Retrieved passage",
                      publisher=c.get("source") or "Databricks corpus",
                      section_path=c.get("category") or "", url=c.get("url") or "",
                      text=c["chunk_text"], licence="", chunk_id=c.get("chunk_id"))
                 for i, c in enumerate(chunks, 1)]
    return dict(question=question, route=route, confidence=confidence, answer=answer,
                chunks_used=len(chunks), chunks=chunks, refused=not chunks,
                citations=citations, answer_style="transformers",
                refusal_reason="insufficient_evidence" if not chunks else None,
                latency_ms=round((perf_counter() - started) * 1000, 2))
