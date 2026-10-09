"""Offline integration contracts for the original default, not live inference tests."""
import sys
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
from app.config import Settings, settings
from app.main import AskRequest, create_app


def test_original_default_and_environment_overrides(monkeypatch):
    monkeypatch.delenv('BACKEND_MODE', raising=False)
    monkeypatch.delenv('MODEL_NAME', raising=False)
    configured = Settings()
    assert configured.BACKEND_MODE == 'databricks'
    assert configured.MODEL_NAME == 'meta-llama/Llama-3.2-1B-Instruct'
    monkeypatch.setenv('TOP_K', '3')
    monkeypatch.setenv('CLASSIFIER_THRESHOLD', '0.7')
    assert Settings().TOP_K == 3
    assert Settings().CLASSIFIER_THRESHOLD == 0.7


def test_default_api_uses_original_http_payloads_and_generator(monkeypatch):
    from app import databricks_client
    from llm import llm
    monkeypatch.setattr(settings, 'BACKEND_MODE', 'databricks')
    for name, value in {'DATABRICKS_HOST': 'https://fixture.example',
                        'DATABRICKS_TOKEN': 'fixture-token',
                        'CLASSIFIER_ENDPOINT': 'router', 'RETRIEVER_ENDPOINT': 'retriever'}.items():
        monkeypatch.setattr(settings, name, value)
    chunk = {'chunk_text': 'Full evidence text.', 'category': 'condition', 'title': 'Fixture'}
    responses = [{'predictions': [{'route': 'condition', 'confidence': 0.91}]},
                 {'predictions': [{'chunks': [chunk]}]}]
    post = Mock(side_effect=[SimpleNamespace(raise_for_status=lambda: None, json=lambda r=r: r)
                             for r in responses])
    monkeypatch.setattr(databricks_client.requests, 'post', post)
    generate = Mock(return_value='Fixture LLaMA response.')
    monkeypatch.setattr(llm, 'answer_with_llm', generate)
    api = TestClient(create_app())
    response = api.post('/ask', json={'question': 'What is diabetes?'})
    assert response.status_code == 200
    data = response.json()
    assert data['mode'] == 'databricks' and data['answer_style'] == 'transformers'
    assert data['citations'][0]['text'] == chunk['chunk_text']
    assert data['claims'] == []  # do not invent sentence-level grounding
    generate.assert_called_once_with('What is diabetes?', [chunk])
    request = AskRequest(question='What is diabetes?')
    assert post.call_args_list[0].args[0] == 'https://fixture.example/serving-endpoints/router/invocations'
    assert post.call_args_list[0].kwargs['json'] == {'dataframe_records': [
        {'question': request.question, 'threshold': request.threshold}]}
    assert post.call_args_list[1].kwargs['json'] == {'dataframe_records': [
        {'question': request.question, 'top_k': request.top_k,
         'pool_k': request.pool_k, 'max_dist': request.max_dist}]}
    assert 'answer-style' not in api.get('/').text


def test_no_silent_switch_to_local_generation():
    api = TestClient(create_app('databricks'))
    assert api.get('/search', params={'q': 'diabetes'}).status_code == 404
    for style in ('ollama', 'excerpts'):
        assert api.post('/ask', json={'question': 'What is diabetes?', 'answer_style': style}).status_code == 422


def test_transformers_wrapper_preserves_original_model_prompt_and_cache(monkeypatch):
    from llm import llm
    from llm.prompt import SYSTEM_PROMPT
    tokenizer = Mock(eos_token='eos')
    tokenizer.apply_chat_template.return_value = 'formatted chat'
    factory = Mock(return_value=Mock(return_value=[{'generated_text': ' Answer. '}]))
    auto_tokenizer = Mock(from_pretrained=Mock(return_value=tokenizer))
    auto_model = Mock(from_pretrained=Mock(return_value=object()))
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(float32='float32'))
    monkeypatch.setitem(sys.modules, 'transformers', SimpleNamespace(
        AutoTokenizer=auto_tokenizer, AutoModelForCausalLM=auto_model, pipeline=factory))
    monkeypatch.setattr(llm, '_pipe', None)
    monkeypatch.setattr(llm, '_tokenizer', None)
    monkeypatch.setattr(llm, 'MODEL_NAME', 'meta-llama/Llama-3.2-1B-Instruct')
    assert llm.answer_with_llm('Question?', [{'chunk_text': 'Evidence.'}]) == 'Answer.'
    assert auto_model.from_pretrained.call_args.args[0] == 'meta-llama/Llama-3.2-1B-Instruct'
    assert auto_model.from_pretrained.call_args.kwargs['device_map'] == 'cpu'
    messages = tokenizer.apply_chat_template.call_args.args[0]
    assert messages == [{'role': 'system', 'content': SYSTEM_PROMPT},
                        {'role': 'user', 'content': 'Context:\nEvidence.\n\nQuestion: Question?'}]
    assert factory.call_args.kwargs['do_sample'] is False
    llm.answer_with_llm('Again?', ['Evidence.'])
    assert factory.call_count == 1


def test_remote_doctor_does_not_expose_credentials(monkeypatch):
    from app.remote_check import inspect
    monkeypatch.setattr(settings, 'DATABRICKS_TOKEN', 'fixture-private-value')
    monkeypatch.setattr(settings, 'CLASSIFIER_ENDPOINT', '')
    result = inspect()
    assert not result['ok'] and not result['live_verified']
    assert 'fixture-private-value' not in str(result)


def test_simultaneous_first_requests_load_model_once(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import time
    from llm import llm
    tokenizer = Mock(eos_token='eos')
    tokenizer.apply_chat_template.return_value = 'prompt'
    def slow_model(*args, **kwargs):
        time.sleep(0.02)
        return object()
    model = Mock(from_pretrained=Mock(side_effect=slow_model))
    pipe = Mock(return_value=[{'generated_text': 'Answer'}])
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(float32='float32'))
    monkeypatch.setitem(sys.modules, 'transformers', SimpleNamespace(
        AutoTokenizer=Mock(from_pretrained=Mock(return_value=tokenizer)),
        AutoModelForCausalLM=model, pipeline=Mock(return_value=pipe)))
    monkeypatch.setattr(llm, '_pipe', None)
    monkeypatch.setattr(llm, '_tokenizer', None)
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: llm.answer_with_llm('Question', ['Evidence']), range(4)))
    assert results == ['Answer'] * 4
    assert model.from_pretrained.call_count == 1


def test_live_probe_uses_configured_retrieval_settings(monkeypatch):
    from app import remote_check, rag, databricks_client
    from llm import llm
    for name, value in {'DATABRICKS_HOST': 'https://example.com', 'DATABRICKS_TOKEN': 'fixture',
                        'CLASSIFIER_ENDPOINT': 'c', 'RETRIEVER_ENDPOINT': 'r',
                        'TOP_K': 3, 'POOL_K': 12, 'MAX_DIST': 0.7}.items():
        monkeypatch.setattr(settings, name, value)
    monkeypatch.setattr(remote_check.importlib.metadata, 'version', lambda _: 'fixture')
    monkeypatch.setattr(databricks_client, 'DatabricksClient', Mock())
    monkeypatch.setattr(llm, 'answer_with_llm', Mock())
    answer = Mock(return_value={'chunks_used': 3, 'refused': False})
    monkeypatch.setattr(rag, 'answer_question', answer)
    assert remote_check.inspect(live=True)['live_verified']
    assert answer.call_args.kwargs == dict(threshold=settings.CLASSIFIER_THRESHOLD,
                                          top_k=3, pool_k=12, max_dist=0.7)


def test_invalid_configured_defaults_are_rejected():
    from pydantic import Field, ValidationError
    import pytest
    class BadDefaults(AskRequest):
        top_k: int = Field(default=0, ge=1, le=20)
    with pytest.raises(ValidationError):
        BadDefaults(question='What is diabetes?')
