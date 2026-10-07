"""Transparent local routing baseline; not a trained medical classifier."""
import re

DRUG = {'medication', 'medicine', 'drug', 'tablet', 'ibuprofen', 'metformin', 'insulin', 'dosage', 'medicines', 'medications', 'drugs', 'tablets'}
CONDITION = {'diabetes', 'symptom', 'symptoms', 'disease', 'condition', 'prediabetes', 'glucose', 'kidney', 'kidneys', 'ckd', 'gfr', 'albumin', 'glomerulus'}


def route_question(question: str) -> dict:
    """Route unambiguous cues; keep mixed and unknown questions unrestricted."""
    words = set(re.findall(r'\w+', question.lower()))
    drug = sorted(words & DRUG)
    condition = sorted(words & CONDITION)
    route = 'drug' if drug and not condition else 'condition' if condition and not drug else 'all'
    return {'category': route, 'method': 'rules', 'matched_terms': sorted(drug + condition)}


def reciprocal_rank_fusion(rankings: list[list[tuple[str, float]]], constant: int = 60):
    """Fuse unique results by rank, ignoring incompatible BM25/cosine score scales."""
    if constant <= 0:
        raise ValueError('RRF constant must be positive')
    scores = {}
    for ranking in rankings:
        seen = set()
        for rank, (key, _) in enumerate(ranking, 1):
            if key in seen:
                continue
            seen.add(key)
            scores[key] = scores.get(key, 0) + 1 / (constant + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))
