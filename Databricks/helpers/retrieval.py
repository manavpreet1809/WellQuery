from typing import List, Dict, Optional, Tuple
import re
import hashlib

def normalize_text(s: str) -> str:
    s = (s or "").lower() # ensure input is string
    s = re.sub(r"\s+", " ", s).strip() # remove extra spaces
    return s

# remove duplicated text across all documents
def text_hash(s: str) -> str:
    return hashlib.md5(normalize_text(s).encode("utf-8")).hexdigest()

def search_chunks_local(question: str, vectorizer, knn, chunks_pdf, top_k: int = 5, pool_k: int = 50, max_dist: float = 0.85) -> List[Dict]:
    question_vector = vectorizer.transform([question]) # convert question to vector
    pool_k = min(pool_k, len(chunks_pdf)) # limit pool size
    distances, indices = knn.kneighbors(question_vector, n_neighbors=pool_k) # find nearest neighbors
    seen_text = set() # track identical/near-identical chunk text
    seen_doc = set() # track document level duplicates
    results: List[Dict] = []
    rank = 0 # ranking counter

    for idx, dist in zip(indices[0], distances[0]):
        # skip weak matches (higher distance is worse)
        if dist > max_dist:
            continue

        row = chunks_pdf.iloc[int(idx)] # get row from chunks df
        doc_id = row.get("doc_id", None) # get doc_id
        h = text_hash(row.get("chunk_text") or "") # dedupe identical/near-identical chunk text

        if h in seen_text:
            continue

        # dedupe multiple chunks from the same doc
        if doc_id is not None and doc_id in seen_doc:
            continue
        
        # mark chunk text as seen
        seen_text.add(h)
        if doc_id is not None:
            seen_doc.add(doc_id)

        # increment rank and append the result
        rank += 1
        results.append({
            "rank": rank, # ranking position based on cosine distance
            "chunk_id": row["chunk_id"], 
            "doc_id": doc_id,
            "title": row.get("title"),
            "source": row.get("source"),
            "category": row.get("category"),
            "cosine_distance": float(dist), # cosine distance score
            "cosine_similarity": float(1.0 - float(dist)), # cosine similarity score
            "chunk_text_preview": (row.get("chunk_text") or "")[:300], # short text preview
        })

        # stop when there is enough results
        if len(results) >= top_k:
            break

    return results