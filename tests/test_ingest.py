import json
import sqlite3
from pathlib import Path
import pytest
from app.ingest import Source, chunk_sections, extract_sections, ingest, load_catalogue, Downloader

@pytest.fixture
def corpus(tmp_path):
    source = dict(id='fixture', title='Fixture', publisher='WellQuery test authors',
                  url='https://example.com/fixture', licence='Original test fixture',
                  licence_url='https://example.com/terms', permission_checked_on='2026-10-02',
                  approved=True, category='all', format='html', selector='article')
    catalogue = tmp_path / 'sources.json'
    catalogue.write_text(json.dumps([source]))
    raw = tmp_path / 'raw'
    raw.mkdir()
    (raw / 'fixture.html').write_text('<nav>Outside</nav><article><h1>One</h1><p>Alpha beta gamma delta.</p><h2>Two</h2><p>Other text.</p><script>Hidden</script><nav>Inside nav</nav><figure>Image credit</figure></article>')
    return catalogue, raw, tmp_path / 'db.sqlite3'

def test_ingest_metadata_sections_and_repeat(corpus):
    catalogue, raw, db = corpus
    first = ingest(*corpus)
    assert first['documents_changed'] == 1
    assert first['total_chunks'] == 2
    assert ingest(*corpus)['documents_changed'] == 0
    with sqlite3.connect(db) as conn:
        metadata = json.loads(conn.execute('SELECT metadata FROM documents').fetchone()[0])
        chunks = conn.execute('SELECT section_path, chunk_text FROM chunks ORDER BY chunk_index').fetchall()
    assert metadata['publisher'] == 'WellQuery test authors'
    assert metadata['retrieved_at'] is None  # local fixtures must not invent retrieval dates
    assert chunks == [('One', 'Alpha beta gamma delta.'), ('One > Two', 'Other text.')]

def test_changed_content_replaces_old_chunks(corpus):
    ingest(*corpus)
    (corpus[1] / 'fixture.html').write_text('<article><p>Replacement only.</p></article>')
    assert ingest(*corpus)['total_chunks'] == 1
    with sqlite3.connect(corpus[2]) as conn:
        assert conn.execute('SELECT chunk_text FROM chunks').fetchone()[0] == 'Replacement only.'

def test_metadata_change_reingests(corpus):
    ingest(*corpus)
    sources = json.loads(corpus[0].read_text())
    sources[0]['title'] = 'Corrected title'
    corpus[0].write_text(json.dumps(sources))
    assert ingest(*corpus)['documents_changed'] == 1

def test_invalid_second_source_leaves_existing_database_intact(corpus):
    ingest(*corpus)
    before = corpus[2].read_bytes()
    sources = json.loads(corpus[0].read_text())
    sources.append({**sources[0], 'id': 'missing'})
    corpus[0].write_text(json.dumps(sources))
    with pytest.raises(ValueError, match='Missing cached'):
        ingest(*corpus)
    assert corpus[2].read_bytes() == before

@pytest.mark.parametrize('kind', ['duplicate', 'unapproved', 'licence'])
def test_bad_catalogue_rejected(corpus, kind):
    items = json.loads(corpus[0].read_text())
    if kind == 'duplicate': items.append(items[0])
    if kind == 'unapproved': items[0]['approved'] = False
    if kind == 'licence': del items[0]['licence']
    corpus[0].write_text(json.dumps(items))
    with pytest.raises(ValueError): load_catalogue(corpus[0])

def test_chunk_bounds_and_section_isolation():
    chunks = list(chunk_sections([('A', 'one two three four five six seven'), ('B', 'last section')], 4, 1))
    assert chunks == [('A', 'one two three four'), ('A', 'four five six seven'), ('B', 'last section')]
    with pytest.raises(ValueError): list(chunk_sections([('A', 'text')], 4, 4))

def test_missing_selector_fails_closed(corpus):
    source = load_catalogue(corpus[0])[0]
    with pytest.raises(ValueError, match='selector'):
        extract_sections('<p>No article</p>', source)

def test_empty_source_does_not_replace_document(corpus):
    ingest(*corpus)
    (corpus[1] / 'fixture.html').write_text('<article></article>')
    with pytest.raises(ValueError, match='No article'): ingest(*corpus)
    with sqlite3.connect(corpus[2]) as conn:
        assert conn.execute('SELECT count(*) FROM chunks').fetchone()[0] == 2

def test_robots_denial_prevents_article_download(corpus, monkeypatch):
    calls = []
    def read(self, url):
        calls.append(url)
        return b'User-agent: *\nDisallow: /\n'
    monkeypatch.setattr(Downloader, 'read', read)
    with pytest.raises(ValueError, match='robots'):
        Downloader().fetch(load_catalogue(corpus[0])[0])
    assert calls == ['https://example.com/robots.txt']

def test_receipt_tampering_rejected(corpus):
    (corpus[1] / 'fixture.receipt.json').write_text(json.dumps({'sha256': 'wrong', 'url': 'https://example.com/fixture'}))
    with pytest.raises(ValueError, match='mismatch'): ingest(*corpus)
