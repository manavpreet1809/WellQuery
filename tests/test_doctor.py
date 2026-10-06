import importlib.metadata
from app.doctor import inspect
from app.search import build_index
from test_search import db, embed


def test_missing_store_is_actionable(tmp_path,monkeypatch):
    monkeypatch.setattr(importlib.metadata,'version',lambda name:'test')
    result=inspect(tmp_path/'missing')
    assert not result['ok']
    assert any('make ingest' in c['detail'] for c in result['checks'])
    assert not result['model_load_tested']


def test_ready_store_does_not_claim_live_model_validation(db,monkeypatch):
    monkeypatch.setattr(importlib.metadata,'version',lambda name:'test')
    build_index(db,embed)
    result=inspect(db)
    assert result['ok'] and not result['model_load_tested']
    assert 'does not validate' in result['scope']


def test_missing_optional_dependency_reported(db,monkeypatch):
    def version(name):
        if name=='sentence-transformers':raise importlib.metadata.PackageNotFoundError(name)
        return 'test'
    monkeypatch.setattr(importlib.metadata,'version',version)
    build_index(db,embed)
    assert not inspect(db)['ok']
