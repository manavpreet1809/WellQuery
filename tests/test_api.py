import pytest
from fastapi.testclient import TestClient
from app.main import create_app

class Client:
    def classify(self, question, threshold):
        return {'predictions': [{'route': 'drug', 'confidence': 0.9}]}
    def retrieve(self, question, *args):
        return {'predictions': [{'chunks': [
            {'chunk_text': 'A fixture passage.', 'category': 'drug'},
            {'chunk_text': 'Another passage.', 'category': 'condition'}]}]}

def test_demo_without_credentials():
    client = TestClient(create_app('demo'))
    assert client.get('/').status_code == 200
    assert 'WellQuery' in client.get('/ui').text
    assert client.get('/static/chat.js').status_code == 200
    assert client.get('/health').json()['mode'] == 'demo'
    result = client.post('/ask', json={'question': 'What is WellQuery?'}).json()
    assert result['mode'] == 'demo' and 'scripted' in result['answer']
    assert client.post('/ask', json={'question': 'Tell me about symptoms'}).json()['refused']

@pytest.mark.parametrize('payload', [
    {'question': '  '}, {'question': 'x' * 1001}, {'question': 'x', 'top_k': 0},
    {'question': 'x', 'threshold': 2}, {'question': 'x', 'pool_k': 2, 'top_k': 3},
])
def test_invalid_input(payload):
    assert TestClient(create_app('demo')).post('/ask', json=payload).status_code == 422

def test_injected_end_to_end_pipeline():
    calls = []
    def generate(question, chunks):
        calls.append((question, chunks))
        return 'A fixture answer.'
    client = TestClient(create_app('databricks', Client(), generate))
    result = client.post('/ask', json={'question': '  fixture question  '})
    assert result.status_code == 200
    assert result.json()['chunks_used'] == 1
    assert calls[0][0] == 'fixture question'
    assert calls[0][1][0]['category'] == 'drug'

@pytest.mark.parametrize('chunks', [[], [{'chunk_text_preview': 'Preview only'}], [{'chunk_text': '  '}]])
def test_no_full_evidence_never_calls_generator(chunks):
    class Empty(Client):
        def retrieve(self, *args):
            return {'predictions': [{'chunks': chunks}]}
    def forbidden(*args):
        pytest.fail('Generator must not run without evidence')
    response = TestClient(create_app('databricks', Empty(), forbidden)).post('/ask', json={'question': 'x'})
    assert response.status_code == 200
    assert response.json()['refused']

def test_errors_do_not_expose_upstream_details():
    class Broken(Client):
        def classify(self, *args):
            raise ValueError('secret-token-and-query')
    response = TestClient(create_app('databricks', Broken(), lambda *a: 'x')).post('/ask', json={'question': 'x'})
    assert response.status_code == 502
    assert 'secret' not in response.text

def test_missing_remote_config_is_service_unavailable(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, 'DATABRICKS_TOKEN', '')
    response = TestClient(create_app('databricks')).post('/ask', json={'question': 'x'})
    assert response.status_code == 503
