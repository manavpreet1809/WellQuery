import json
import sqlite3
import pytest
from app.search import search, build_index, keyword_rank

@pytest.fixture
def db(tmp_path):
    path=tmp_path/'docs.sqlite3'
    with sqlite3.connect(path) as c:
        c.execute('CREATE TABLE documents(id TEXT PRIMARY KEY,metadata TEXT)')
        c.execute('CREATE TABLE chunks(id TEXT,document_id TEXT,section_path TEXT,chunk_text TEXT)')
        for key,text,category in [('a','Blood glucose and diabetes','condition'),('b','Medicine tablet information','drug'),('c','General wellness overview','all')]:
            c.execute('INSERT INTO documents VALUES (?,?)',(key,json.dumps(dict(title=key,publisher='Fixture',url='https://example.com/'+key,licence='Fixture',category=category))))
            c.execute('INSERT INTO chunks VALUES (?,?,?,?)',(key,key,'Overview',text))
    return path

def embed(texts):
    return [[1.,0.] if 'glucose' in t.lower() or 'sugar' in t.lower() else [0.,1.] for t in texts]

def test_keyword_ranks_and_metadata(db):
    hit=search('glucose',database=db)[0]
    assert hit['chunk_id']=='a' and hit['publisher']=='Fixture'
    assert search('unknownxyz',database=db)==[]
    assert search('" OR DROP TABLE chunks; --',database=db)==[]

def test_vector_paraphrase_and_staleness(db):
    assert build_index(db,embed)==3
    assert search('sugar',mode='vector',database=db,embed=embed)[0]['chunk_id']=='a'
    with sqlite3.connect(db) as c: c.execute("UPDATE chunks SET chunk_text='changed' WHERE id='a'")
    with pytest.raises(RuntimeError,match='stale'): search('sugar','vector',database=db,embed=embed)

def test_keyword_needs_no_model_and_vector_needs_index(db):
    assert search('tablet',database=db)[0]['chunk_id']=='b'
    with pytest.raises(RuntimeError,match='missing'): search('tablet','vector',database=db,embed=embed)

@pytest.mark.parametrize('query,k',[('',5),('  ',5),('a'*1001,5),('test',0),('test',21)])
def test_validation(db,query,k):
    with pytest.raises(ValueError): search(query,k=k,database=db)

def test_failed_index_preserves_previous(db):
    build_index(db,embed)
    with pytest.raises(ValueError): build_index(db,lambda texts:[[0.,0.] for t in texts])
    assert search('sugar','vector',database=db,embed=embed)[0]['chunk_id']=='a'

from app.search import search_report
from app.routing import route_question, reciprocal_rank_fusion
from app.main import create_app
from fastapi.testclient import TestClient

def test_rrf_hand_calculated():
    result=dict(reciprocal_rank_fusion([[('a',99),('b',1)],[('b',0.9),('c',0.8)]]))
    assert result['b']==pytest.approx(1/62+1/61)
    assert result['a']==pytest.approx(1/61)
    assert reciprocal_rank_fusion([])==[]
    assert reciprocal_rank_fusion([[('a',1),('a',1)]])==[('a',1/61)]

@pytest.mark.parametrize('question,expected', [('medicine tablet','drug'),('diabetes symptoms','condition'),('insulin for diabetes','all'),('hello','all'),('drugstore opening','all')])
def test_rule_routes(question,expected):
    assert route_question(question)['category']==expected

def test_hybrid_and_routed_comparison(db):
    build_index(db,embed)
    report=search_report('glucose','hybrid',database=db,embed=embed)
    assert report['hits'][0]['chunk_id']=='a'
    assert report['hits'][0]['keyword_rank']==1 and report['hits'][0]['vector_rank']==1
    filtered=search_report('medicine','hybrid',database=db,embed=embed,routing=True)
    assert filtered['route']['method']=='rules'
    assert all(h['category'] in {'drug','all'} for h in filtered['hits'])

def test_no_route_coverage_is_explicit(db):
    with sqlite3.connect(db) as c:
        c.execute("DELETE FROM chunks WHERE id IN ('b','c')")
    report=search_report('medicine',database=db,routing=True)
    assert report['hits']==[] and report['empty_reason']=='no_documents_for_route'

def test_search_api(db):
    build_index(db,embed)
    api=TestClient(create_app('demo',search_database=db,search_embed=embed))
    result=api.get('/search',params={'q':'glucose','mode':'hybrid','routing':'true'})
    assert result.status_code==200
    assert result.json()['hits'][0]['url']=='https://example.com/a'
    for params in ({'q':' '},{'q':'x','k':100},{'q':'x','mode':'bad'}):
        assert api.get('/search',params=params).status_code==422

def test_search_api_missing_store_returns_actionable_503(tmp_path):
    api=TestClient(create_app('demo',search_database=tmp_path/'missing'))
    response=api.get('/search',params={'q':'glucose'})
    assert response.status_code==503
    assert 'Ingest' in response.json()['detail']
