"""Check local-demo prerequisites without downloading data or changing configuration."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sqlite3
import sys
from app.search import DATABASE, MODEL, REVISION, connect, fingerprint, read_chunks


def inspect(database: Path = DATABASE, smoke: bool = False) -> dict:
    """Return actionable readiness checks; live inference is checked only on request."""
    checks = []
    def add(name, ok, detail):
        checks.append(dict(name=name, ok=ok, detail=detail))
    add('python', sys.version_info >= (3,12), 'Python 3.12+ is required for the documented setup')
    for name in ('fastapi','jinja2','sentence-transformers'):
        try:
            add(name,True,importlib.metadata.version(name))
        except importlib.metadata.PackageNotFoundError:
            add(name,False,'Install requirements-demo.lock')
    try:
        rows=read_chunks(database)
        add('documents',bool(rows),f'{len(rows)} chunks available')
        with connect(database) as conn:
            record=conn.execute('SELECT payload FROM vector_index WHERE id=1').fetchone()
        data=json.loads(record[0]) if record else {}
        current=(data.get('fingerprint')==fingerprint(rows) and data.get('model')==MODEL
                 and data.get('revision')==REVISION and set(data.get('vectors',{}))=={r['chunk_id'] for r in rows})
        add('vector_index',current,'Current snapshot' if current else 'Run make index after ingestion')
    except (OSError,RuntimeError,sqlite3.Error,ValueError,TypeError):
        add('document_store',False,'Run make ingest and make index')
    if smoke and all(c['ok'] for c in checks):
        try:
            from app.answers import answer_local
            from app.main import create_app
            from fastapi.testclient import TestClient
            api=TestClient(create_app('local',search_database=database))
            assert api.get('/').status_code==200
            assert api.get('/evaluation').status_code==200
            answer=answer_local('What is diabetes?',database=database)
            ok=not answer['refused'] and bool(answer['citations'])
            add('local_excerpt_smoke',ok,'Retrieved source excerpts with citations' if ok else 'Demo question has no supported excerpts; check corpus')
        except Exception as exc:
            add('local_excerpt_smoke',False,f'Local check failed ({type(exc).__name__}); verify model cache and document index')
    return dict(ok=all(c['ok'] for c in checks), checks=checks,
                scope='Local excerpt demo only; does not validate medical accuracy or live Ollama/Databricks inference',
                model_load_tested=smoke and any(c['name']=='local_excerpt_smoke' for c in checks))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,default=DATABASE)
    parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args()
    result=inspect(args.database,args.smoke)
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['ok'] else 1)

if __name__=='__main__':main()
