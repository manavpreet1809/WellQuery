"""Small-corpus BM25 and dense-vector retrieval over ingested documents."""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / 'data/processed/wellquery.sqlite3'
MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
# Pin the embedding model independently of application dependencies.
REVISION = 'c9745ed1d9f207416be6d2e6f8de32d1f16199bf'


def connect(database: Path):
    """Require an existing ingestion database; never create an empty one by accident."""
    if not database.is_file():
        raise RuntimeError('Document database missing; run app.ingest first')
    return sqlite3.connect(database)


def read_chunks(database: Path) -> list[dict]:
    """Read full evidence and publisher metadata in a consistent snapshot."""
    with connect(database) as conn:
        rows = conn.execute('SELECT c.id,c.document_id,c.section_path,c.chunk_text,d.metadata FROM chunks c JOIN documents d ON d.id=c.document_id ORDER BY c.id').fetchall()
    return [dict(chunk_id=r[0], document_id=r[1], section_path=r[2], text=r[3],
                 **{k: json.loads(r[4]).get(k) for k in ('title','publisher','url','licence','category')}) for r in rows]


def fingerprint(rows: list[dict]) -> str:
    """Invalidate vectors on content, category, or attribution changes."""
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def tokens(text: str) -> list[str]:
    """Tokenize words without interpreting query text as a search language."""
    return re.findall(r'\w+', text.lower())


def keyword_rank(query: str, rows: list[dict]) -> list[tuple[str, float]]:
    """Rank matching chunks using BM25 (k1=1.5, b=0.75)."""
    terms = set(tokens(query))
    documents = [Counter(tokens(r['text'])) for r in rows]
    if not documents or not terms:
        return []
    lengths = [sum(d.values()) for d in documents]
    average = sum(lengths) / len(lengths) or 1
    frequencies = {t: sum(t in d for d in documents) for t in terms}
    results = []
    for row, doc, length in zip(rows, documents, lengths):
        score = 0.0
        for term in terms:
            tf = doc[term]
            df = frequencies[term]
            idf = math.log(1 + (len(rows) - df + 0.5) / (df + 0.5))
            score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * length / average))
        if score > 0:
            results.append((row['chunk_id'], score))
    return sorted(results, key=lambda item: (-item[1], item[0]))


@lru_cache(maxsize=2)
def encoder(download: bool = False):
    """Load locally by default; only index setup explicitly downloads model files."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL, revision=REVISION, cache_folder=str(ROOT / 'data/models'),
                               local_files_only=not download, device='cpu', trust_remote_code=False)


def encode(texts: list[str], download: bool = False) -> list[list[float]]:
    """Use normalized sentence embeddings; never send text to a hosted inference API."""
    return encoder(download).encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def unit(vector: list[float]) -> list[float]:
    """Validate and normalize stored and query vectors."""
    if not vector or any(not math.isfinite(x) for x in vector):
        raise ValueError('Invalid vector')
    norm = math.sqrt(sum(x*x for x in vector))
    if norm == 0:
        raise ValueError('Zero vector')
    return [x / norm for x in vector]


def build_index(database: Path = DATABASE, embed=None, download: bool = False) -> int:
    """Atomically replace the vector snapshot; content hash detects later ingestion."""
    rows = read_chunks(database)
    if not rows:
        raise RuntimeError('No chunks to index')
    vectors = (embed or (lambda texts: encode(texts, download)))([r['text'] for r in rows])
    if len(vectors) != len(rows):
        raise ValueError('Embedding count mismatch')
    vectors = [unit(v) for v in vectors]
    if len({len(v) for v in vectors}) != 1:
        raise ValueError('Embedding dimension mismatch')
    payload = json.dumps(dict(fingerprint=fingerprint(rows), model=MODEL, revision=REVISION,
                             vectors={r['chunk_id']: v for r,v in zip(rows,vectors)}))
    with connect(database) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS vector_index (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
        conn.execute('INSERT OR REPLACE INTO vector_index VALUES (1,?)', (payload,))
    return len(rows)


def vector_rank(query: str, rows: list[dict], database: Path, embed=None):
    """Exact cosine ranking, appropriate for the small student-project corpus."""
    with connect(database) as conn:
        try:
            record = conn.execute('SELECT payload FROM vector_index WHERE id=1').fetchone()
        except sqlite3.OperationalError:
            record = None
    if record is None:
        raise RuntimeError('Vector index missing; run python -m app.search --index --download-model')
    index = json.loads(record[0])
    if (index['fingerprint'] != fingerprint(rows) or index['model'] != MODEL or index['revision'] != REVISION):
        raise RuntimeError('Vector index stale; rebuild with python -m app.search --index')
    q = unit((embed or encode)([query])[0])
    results = []
    for row in rows:
        v = index['vectors'][row['chunk_id']]
        if len(q) != len(v):
            raise RuntimeError('Vector dimension mismatch; rebuild index')
        results.append((row['chunk_id'], sum(a*b for a,b in zip(q,v))))
    return sorted(results, key=lambda item: (-item[1], item[0]))


def search_report(query: str, mode: str = 'hybrid', k: int = 5, database: Path = DATABASE,
                  embed=None, routing: bool = False) -> dict:
    """Compare retrieval modes with optional, explicitly labeled rule-based routing."""
    from time import perf_counter
    from app.routing import reciprocal_rank_fusion, route_question
    started = perf_counter()
    if not query.strip() or len(query) > 1000 or not 1 <= k <= 20:
        raise ValueError('Require a question of 1–1000 characters and k of 1–20')
    if mode not in {'keyword', 'vector', 'hybrid'}:
        raise ValueError('Unknown search mode')
    rows = read_chunks(database)
    route = route_question(query) if routing else dict(category='all', method='disabled', matched_terms=[])
    eligible = {r['chunk_id'] for r in rows if route['category'] == 'all' or r['category'] in {route['category'], 'all'}}
    # Keep the full corpus for vector freshness validation; then restrict candidates.
    keyword = keyword_rank(query, rows) if mode != 'vector' else []
    vector = vector_rank(query, rows, database, embed) if mode != 'keyword' and eligible else []
    keyword = [(key, score) for key, score in keyword if key in eligible][:50]
    vector = [(key, score) for key, score in vector if key in eligible][:50]
    ranking = reciprocal_rank_fusion([keyword, vector]) if mode == 'hybrid' else keyword if mode == 'keyword' else vector
    lookup = {r['chunk_id']: r for r in rows}
    kr = {key: rank for rank, (key, _) in enumerate(keyword, 1)}
    vr = {key: rank for rank, (key, _) in enumerate(vector, 1)}
    hits = [{**lookup[key], 'score': score, 'keyword_rank': kr.get(key), 'vector_rank': vr.get(key)} for key, score in ranking[:k]]
    return dict(mode=mode, route=route, hits=hits, latency_ms=round((perf_counter()-started)*1000, 2),
                empty_reason=('no_documents_for_route' if rows and not eligible else 'no_matches') if not hits else None)


def search(query: str, mode: str = 'keyword', k: int = 5, database: Path = DATABASE, embed=None) -> list[dict]:
    """Compatibility helper returning passages only."""
    return search_report(query, mode, k, database, embed)['hits']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', nargs='?')
    parser.add_argument('--mode', choices=['keyword','vector','hybrid'], default='keyword')
    parser.add_argument('--database', type=Path, default=DATABASE)
    parser.add_argument('--routing', action='store_true')
    parser.add_argument('--index', action='store_true')
    parser.add_argument('--download-model', action='store_true')
    args = parser.parse_args()
    try:
        if args.index:
            print(json.dumps({'indexed_chunks': build_index(args.database, download=args.download_model)}))
        elif args.query:
            print(json.dumps(search_report(args.query, args.mode, database=args.database, routing=args.routing), indent=2))
        else:
            parser.error('Supply a query or --index')
    except (RuntimeError, ImportError, OSError, ValueError) as exc:
        parser.exit(1, f'Search unavailable: {exc}\n')

if __name__ == '__main__':
    main()
