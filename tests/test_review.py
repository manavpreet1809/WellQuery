import json
import pytest
from evaluation.review import export_packet, apply_packet, summarize_answers
from test_search import db
from test_evaluation import question

@pytest.fixture
def packet(tmp_path,db):
    source=tmp_path/'questions.jsonl';source.write_text(json.dumps(question())+'\n')
    output=tmp_path/'packet.json';export_packet(source,output,db)
    return source,output,tmp_path/'reviewed.jsonl'

def approve(packet):
    data=json.loads(packet[1].read_text())
    data['items'][0].update(decision='approve',reviewer='Test reviewer',notes='Reviewed fixture labels')
    packet[1].write_text(json.dumps(data))

def test_export_does_not_verify_and_noop_is_rejected(packet):
    data=json.loads(packet[1].read_text())
    assert data['items'][0]['decision'] is None and data['items'][0]['evidence']
    with pytest.raises(ValueError,match='No review'):apply_packet(*packet)
    assert not packet[2].exists()

def test_apply_preserves_original_and_output_is_exclusive(packet):
    before=packet[0].read_bytes();approve(packet)
    assert apply_packet(*packet)['verified_questions']==1
    assert packet[0].read_bytes()==before
    with pytest.raises(FileExistsError):apply_packet(*packet)

def test_stale_packet_rejected(packet):
    approve(packet);packet[0].write_text(packet[0].read_text()+'\n')
    with pytest.raises(ValueError,match='Stale'):apply_packet(*packet)

@pytest.mark.parametrize('field,value',[('reviewer',''),('notes',''),('decision','yes')])
def test_invalid_decision_rejected_without_output(packet,field,value):
    approve(packet);data=json.loads(packet[1].read_text());data['items'][0][field]=value
    packet[1].write_text(json.dumps(data))
    with pytest.raises(ValueError):apply_packet(*packet)
    assert not packet[2].exists()

def test_answer_summary_does_not_call_unreviewed_answers_correct(tmp_path):
    path=tmp_path/'answers.jsonl'
    row=dict(id='a',actual='answer',human_claim_support=None,human_relevance=None,reviewer=None)
    path.write_text(json.dumps(row)+'\n')
    assert summarize_answers(path)['supported_fraction_of_reviewed_answers'] is None
    row.update(human_claim_support='uncertain',human_relevance='relevant',reviewer='Test reviewer')
    path.write_text(json.dumps(row)+'\n')
    assert summarize_answers(path)['supported_fraction_of_reviewed_answers']==0
    assert summarize_answers(path)['support_counts']['uncertain']==1
