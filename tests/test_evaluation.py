import json
import pytest
from evaluation.run import load_questions, retrieval_metrics, percentile95, run
from test_search import db


def question():
    return dict(id='q1',group='topic',split='test',question='glucose',verified=False,reviewer=None,
                expected='answer',expected_route='condition',relevant=[dict(document_id='a',section_path='Overview')])

def test_verified_gate_and_review_attribution(tmp_path):
    p=tmp_path/'questions.jsonl';q=question();p.write_text(json.dumps(q)+'\n')
    with pytest.raises(ValueError,match='No human'): load_questions(p)
    assert len(load_questions(p,True))==1
    q['verified']=True;p.write_text(json.dumps(q)+'\n')
    with pytest.raises(ValueError,match='reviewer'): load_questions(p)
    q['reviewer']='Test fixture reviewer';p.write_text(json.dumps(q)+'\n')
    assert len(load_questions(p))==1

def test_paraphrase_leakage_rejected(tmp_path):
    p=tmp_path/'questions.jsonl';q=question()
    p.write_text(json.dumps(q)+'\n'+json.dumps({**q,'id':'q2','split':'development'}))
    with pytest.raises(ValueError,match='Paraphrase'):load_questions(p,True)

def test_metrics_deduplicate_sections():
    relevant=[dict(document_id='a',section_path='one'),dict(document_id='b',section_path='two')]
    hits=[dict(document_id='x',section_path='bad')]+[relevant[0]]*3
    assert retrieval_metrics(hits,relevant)=={'recall_at_5':.5,'reciprocal_rank_at_5':.5}
    assert percentile95([1,2,3,100])==100

def test_export_labels_drafts_and_leaves_human_fields_empty(db,tmp_path,monkeypatch):
    import evaluation.run as module
    monkeypatch.setattr(module,'search_report',lambda *a,**k:dict(hits=[dict(document_id='a',section_path='Overview')],latency_ms=1))
    monkeypatch.setattr(module,'answer_local',lambda *a,**k:dict(refused=False,refusal_reason=None,answer='Fixture',citations=[],claims=[]))
    output=tmp_path/'results'
    summary=run([question()],db,output)
    assert summary['verified_question_count']==0
    assert summary['label']=='DRAFT DEVELOPMENT RESULTS'
    assert len(summary['configurations'])==4
    review=json.loads((output/'answer_review.jsonl').read_text())
    assert review['human_claim_support'] is None
    assert review['quote_validity'] is None
    with pytest.raises(FileExistsError):run([question()],db,output)
