"""Check the default MediBot configuration; --live explicitly calls both endpoints and LLaMA."""
import argparse
import importlib.metadata
import json
from app.config import settings

# Plain-language causes for serving-endpoint HTTP failures; no host or token is ever echoed.
HTTP_HINTS = {
    400: 'rejected the request format; check the model signature matches the original payload',
    401: 'rejected the token; check DATABRICKS_TOKEN',
    403: 'denied access; the token needs Can Query permission on this endpoint',
    404: 'was not found; check the endpoint name or create it (Databricks/README.md)',
    429: 'is rate limited; wait and retry',
}


def _huggingface_access():
    """Gated LLaMA weights need a token; the hub also reads HF_TOKEN or a saved login."""
    if settings.HF_TOKEN:
        return True, 'HF_TOKEN configured'
    try:
        from huggingface_hub import get_token
        if get_token():
            return True, 'Saved Hugging Face login found'
    except ImportError:
        return False, 'Run make setup'
    if not settings.MODEL_NAME.startswith('meta-llama/'):
        return True, 'No token; assuming the configured model is public'
    return False, 'Set HF_TOKEN in .env after Meta approves access to the model'


def _explain_failure(exc):
    """Name the failing stage so a live smoke failure is actionable."""
    import requests
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        url = exc.response.url or ''
        endpoint = url.split('/serving-endpoints/')[1].split('/')[0] if '/serving-endpoints/' in url else 'endpoint'
        code = exc.response.status_code
        hint = HTTP_HINTS.get(code, 'returned a server error; it may still be starting, check its Serving logs')
        return f'Databricks endpoint "{endpoint}" {hint} (HTTP {code})'
    if isinstance(exc, requests.Timeout):
        return 'A Databricks endpoint did not answer within 60s; a scaled-to-zero endpoint can take several minutes to start, so retry'
    if isinstance(exc, requests.ConnectionError):
        return 'Could not reach DATABRICKS_HOST; check the URL and your network'
    if isinstance(exc, ValueError):
        return f'{type(exc).__name__}: an endpoint returned an unexpected response shape'
    if isinstance(exc, OSError):
        return f'{type(exc).__name__}: could not load {settings.MODEL_NAME}; check HF_TOKEN and approved model access'
    return f'{type(exc).__name__}: check endpoint access and Hugging Face model access'


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
    hf_ok, hf_detail = _huggingface_access()
    checks.append({'name': 'huggingface_access', 'ok': hf_ok, 'detail': hf_detail})
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
            checks.append({'name': 'live_pipeline', 'ok': False, 'detail': _explain_failure(exc)})
    return {'ok': all(c['ok'] for c in checks), 'model': settings.MODEL_NAME,
            'checks': checks, 'live_verified': verified,
            'scope': 'Configuration checks do not verify endpoint availability or approved model access. Live smoke is not an accuracy evaluation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    result = inspect(parser.parse_args().live)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
