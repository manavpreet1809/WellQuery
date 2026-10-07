import json
from types import SimpleNamespace
import pytest
import requests
from app.synthesis import model_status, request_claims


def response(payload, status=200):
    return SimpleNamespace(status_code=status,json=lambda:payload)


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr('app.synthesis.selected_model',lambda:'fixture')


def test_metadata_is_not_generation():
    calls=[]
    def get(url,**kwargs):
        calls.append((url,kwargs))
        return response({'models':[{'name':'fixture:latest','digest':'abc'}]})
    status=model_status(get)
    assert status['ready'] and status['digest']=='abc'
    assert calls==[('http://127.0.0.1:11434/api/tags',dict(timeout=2,allow_redirects=False))]
    assert 'live' in status['detail']


@pytest.mark.parametrize('payload,code,reason',[
    ({'models':[]},200,'model_not_installed'),
    ({'models':[{'name':'different'}]},200,'model_not_installed'),
    ({},302,'service_error'),([],200,'invalid_metadata'),
    ({'models':None},200,'invalid_metadata')])
def test_readiness_failures(payload,code,reason):
    assert model_status(lambda *a,**k:response(payload,code))['reason']==reason


def test_unavailable_service():
    def get(*a,**k):raise requests.ConnectionError()
    assert model_status(get)['reason']=='service_unreachable'


def test_missing_configuration_never_connects(monkeypatch):
    monkeypatch.setattr('app.synthesis.selected_model',lambda:'')
    def forbidden(*a,**k):pytest.fail('Unexpected network call')
    assert model_status(forbidden)['reason']=='model_not_configured'
    with pytest.raises(RuntimeError):request_claims('question',[dict(chunk_id='a',text='A useful evidence sentence.')],forbidden)


def test_request_contract():
    def post(url,**kwargs):
        assert url=='http://127.0.0.1:11434/api/chat'
        assert kwargs['allow_redirects'] is False
        assert kwargs['timeout']==(3,90)
        assert kwargs['json']['stream'] is False
        assert kwargs['json']['options']['num_predict']==768
        return response({'done':True,'message':{'content':json.dumps({'claims':[]})}})
    assert request_claims('question',[dict(chunk_id='a',text='A useful evidence sentence.')],post)=={'claims':[]}


@pytest.mark.parametrize('payload',[
    {'done':False},{'done':True,'done_reason':'length'},[],{'done':True,'message':None},
    {'done':True,'message':{'content':'not JSON'}},
    {'done':True,'message':{'content':'[]'}},
    {'done':True,'message':{'content':'x'*20001}}])
def test_malformed_generation_rejected(payload):
    with pytest.raises(ValueError):request_claims('question',[dict(chunk_id='a',text='A useful evidence sentence.')],lambda *a,**k:response(payload))


def test_redirect_rejected():
    with pytest.raises(RuntimeError):request_claims('question',[dict(chunk_id='a',text='A useful evidence sentence.')],lambda *a,**k:response({},302))


def test_evidence_ids_map_to_exact_server_quotes():
    payload={'done':True,'message':{'content':json.dumps({'claims':[{'text':'Supported fact','evidence_id':'E1'}]})}}
    result=request_claims('question',[dict(chunk_id='source',text='An exact supporting sentence.')],lambda *a,**k:response(payload))
    assert result['claims']==[dict(text='Supported fact',source_id='source',quote='An exact supporting sentence.')]
    payload['message']['content']=json.dumps({'claims':[{'text':'Fact','evidence_id':'invented'}]})
    with pytest.raises(ValueError,match='Unknown evidence'):
        request_claims('question',[dict(chunk_id='source',text='An exact supporting sentence.')],lambda *a,**k:response(payload))
