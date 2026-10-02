from typing import Any, Dict, List, Optional, Tuple
from app.databricks_client import DatabricksClient
from llm.llm import answer_with_llm

def _first_prediction(response: Dict[str, Any]) -> Dict[str, Any]:
    predictions = response.get("predictions") or []

    if not predictions:
        return {}
    
    return predictions[0] # use only the first prediction

def route_question(dbc: DatabricksClient, question: str, threshold: float = 0.80) -> Tuple[str, float, Dict[str, float]]:
    response = dbc.classify(question=question, threshold=threshold) # call classifier
    p0 = _first_prediction(response) # get first prediction
    route = (p0.get("route") or "all") # choose route: drug | condition | all
    conf = float(p0.get("confidence") or 0.0) # confidence score
    probs = p0.get("probs") or {} # get probs dict
    probs = {str(k): float(v) for k, v in probs.items()} # normalize keys/values to str/float

    return route, conf, probs

def get_chunks(dbc: DatabricksClient, question: str, top_k: int = 5, pool_k: int = 50, max_dist: float = 0.85) -> List[Dict[str, Any]]:
    response = dbc.retrieve(question=question, top_k=top_k, pool_k=pool_k, max_dist=max_dist) # call retriever
    p0 = _first_prediction(response) # get first prediction
    chunks = p0.get("chunks") or [] # get chunks list

    return chunks

def parse_classifier_response(resp: Dict[str, Any]) -> Tuple[str, float]:
    preds = (resp or {}).get("predictions") or [] # get predictions list

    # default to "all" if no predictions
    if not preds:
        return "all", 0.0

    p0 = preds[0]
    route = (p0.get("route") or "all").strip()
    conf = float(p0.get("confidence") or 0.0)

    if route not in {"drug", "condition", "all"}:
        route = "all"

    return route, conf

def filter_chunks_by_route(chunks: List[Dict[str, Any]], route: str) -> List[Dict[str, Any]]:
    # only filter if route is specified
    if route not in {"drug", "condition"}:
        return chunks

    routed = [c for c in chunks if (c.get("category") == route)] # keep only chunks whose category matches the route
    return routed if routed else chunks  # fallback to unfiltered if empty

def answer_question(question: str, *, threshold: float = 0.80, top_k: int = 5, pool_k: int = 50, max_dist: float = 0.85) -> Dict[str, Any]:
    dbc = DatabricksClient()

    # classify
    cls = dbc.classify(question, threshold=threshold)
    route, conf = parse_classifier_response(cls)

    # retrieve
    ret = dbc.retrieve(question, top_k=top_k, pool_k=pool_k, max_dist=max_dist)
    preds = (ret or {}).get("predictions") or []
    chunks = (preds[0].get("chunks") if preds else []) or []

    # route-based filtering
    chunks = filter_chunks_by_route(chunks, route)

    # build context for LLM
    context_texts = [c.get("chunk_text", "") for c in chunks if c.get("chunk_text")]
    answer = answer_with_llm(question, context_texts)

    return {
        "question": question,
        "route": route,
        "route_confidence": conf,
        "top_chunks": chunks,
        "answer": answer,
    }
