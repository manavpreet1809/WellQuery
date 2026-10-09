"""Check the default MediBot configuration; --live explicitly calls both endpoints and LLaMA."""
import argparse
import importlib.metadata
import json
from app.config import settings


def inspect(live=False):
    checks = []
    for key in ('DATABRICKS_HOST', 'DATABRICKS_TOKEN', 'CLASSIFIER_ENDPOINT', 'RETRIEVER_ENDPOINT'):
        checks.append({'name': key, 'ok': bool(getattr(settings, key)),
                       'detail': 'Configured' if getattr(settings, key) else 'Set in .env'})
    checks.append({'name': 'https', 'ok': settings.DATABRICKS_HOST.startswith('https://'),
                   'detail': 'Databricks requires HTTPS'})
    for package in ('transformers', 'torch', 'accelerate'):
        try:
            version = importlib.metadata.version(package)
            checks.append({'name': package, 'ok': True, 'detail': version})
        except importlib.metadata.PackageNotFoundError:
            checks.append({'name': package, 'ok': False, 'detail': 'Run make setup'})
    verified = False
    if live and all(c['ok'] for c in checks):
        try:
            from app.databricks_client import DatabricksClient
            from app.rag import answer_question
            from llm.llm import answer_with_llm
            result = answer_question('What is diabetes?', DatabricksClient(), answer_with_llm,
                                     threshold=settings.CLASSIFIER_THRESHOLD,
                                     top_k=settings.TOP_K, pool_k=settings.POOL_K,
                                     max_dist=settings.MAX_DIST)
            verified = bool(result['chunks_used'] and not result['refused'])
            checks.append({'name': 'live_pipeline', 'ok': verified,
                           'detail': 'Retrieved evidence and generated an answer' if verified else 'No evidence returned'})
        except Exception as exc:
            checks.append({'name': 'live_pipeline', 'ok': False,
                           'detail': f'{type(exc).__name__}: check endpoint access and Hugging Face model access'})
    return {'ok': all(c['ok'] for c in checks), 'model': settings.MODEL_NAME,
            'checks': checks, 'live_verified': verified,
            'scope': 'Configuration checks do not verify endpoint availability or model access. Live smoke is not an accuracy evaluation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    result = inspect(parser.parse_args().live)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
