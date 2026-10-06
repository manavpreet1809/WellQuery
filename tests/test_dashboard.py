import json
from fastapi.testclient import TestClient
from app.main import create_app
from app.dashboard import load_runs


def summary(root, **overrides):
    directory=root/'run1';directory.mkdir(exist_ok=True)
    data=dict(question_count=60,verified_question_count=0,configurations={
        'test/hybrid':dict(n=14,recall_at_5=1.,mrr_at_5=.8,p95_ms=20)},behaviour_checks={},model='<script>alert(1)</script>')
    data.update(overrides)
    (directory/'summary.json').write_text(json.dumps(data))


def test_draft_and_escaping(tmp_path):
    summary(tmp_path)
    page=TestClient(create_app('demo',evaluation_root=tmp_path)).get('/evaluation')
    assert page.status_code==200 and 'Draft development results' in page.text
    assert '0 / 60' in page.text
    assert '<script>alert' not in page.text and '&lt;script&gt;' in page.text


def test_invalid_metrics_are_not_displayed(tmp_path):
    summary(tmp_path,configurations={'test/hybrid':dict(n=1,recall_at_5=float('nan'),mrr_at_5=0,p95_ms=1)})
    assert load_runs(tmp_path)==([],1)


def test_empty_and_unknown_runs(tmp_path):
    api=TestClient(create_app('demo',evaluation_root=tmp_path))
    assert 'No evaluation runs yet' in api.get('/evaluation').text
    assert api.get('/evaluation',params={'run':'../../secret'}).status_code==404


def test_symlink_summary_ignored(tmp_path):
    outside=tmp_path/'outside.json';outside.write_text('{}')
    directory=tmp_path/'run1';directory.mkdir()
    (directory/'summary.json').symlink_to(outside)
    assert load_runs(tmp_path)==([],0)
