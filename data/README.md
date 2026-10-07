# Starter document catalogue

`sources.json` contains 15 NIDDK text articles: diabetes and kidney-health information, including two medication-information pages. The October 7, 2026 ingestion produced 201 chunks. It meets the original minimum document count but is not a balanced or comprehensive clinical dataset. Original three-source evaluation runs remain historical results and are not comparable to expanded-corpus runs without controlling the corpus fingerprint.

The publisher's [copyright policy](https://www.niddk.nih.gov/copyright), checked October 2, 2026, allows reproduction of most site information with acknowledgement and exceptions for third-party content. The selected articles identify NIDDK as their source. The extractor excludes graphics, logos, tables, and surrounding navigation. This is an independent project, not endorsed by NIDDK; the content must not be used to imply endorsement or recommend specific medical advice. Review permissions again when adding sources.

## Ingest

```sh
.venv/bin/python -m app.ingest --download
.venv/bin/python -m app.ingest
# Explicitly retrieve newer versions:
.venv/bin/python -m app.ingest --download --refresh
```

Network access is opt-in. Downloads check robots.txt, identify the project, space requests to each host by at least one second, use timeouts and a 3 MB limit, and reject redirects. Failures require correcting the catalogue or retrying; there is no automatic retry loop.

Raw HTML and retrieval receipts live in ignored `data/raw/`; the database lives in ignored `data/processed/wellquery.sqlite3`. Documents record the title, publisher, original URL, permission URL, permission-review date, retrieval timestamp, SHA-256 content hash, and chunking settings. Local fixture imports have no invented retrieval timestamp.

SQLite is a lightweight interim document store, not a vector index. Chunks use 180-word windows with 30-word overlap and do not cross section boundaries. Windows may split sentences; they are not token-counted. The extractor supports curated HTML selectors and UTF-8 plain text, not PDF or OCR. Missing article selectors and empty extractions fail closed.

Re-ingestion replaces changed documents and skips unchanged ones. All documents are prepared before database writes, and changes are committed in one transaction. Removing a catalogue entry does not automatically delete its existing database rows. Use a fresh database when intentionally reducing the corpus.

This store is connected to `/search` for keyword, vector, and hybrid retrieval, but not yet to local generated answers in `/ask`. The default chat mode remains an explicitly scripted demo.

## Expansion review (October 7, 2026)

Twelve additional pages were discovered through NIDDK navigation and reviewed under the publisher copyright policy. Each selected article identifies NIDDK as its source; no separate copyright notice was found in its extracted article text. Graphics and logos remain excluded. One gestational-diabetes navigation page lacked the article selector and was replaced with its linked Definition & Facts article before ingestion succeeded. Every source records its original URL, publisher, permission URL, and review date. All 15 sources ingest successfully; a cached rerun changed zero documents.
