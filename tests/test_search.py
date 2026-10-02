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
