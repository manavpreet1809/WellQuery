"""Ingest curated HTML/text sources into a local SQLite document store."""
import argparse
import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

USER_AGENT = "WellQueryStudent/0.1 (+https://github.com/manavpreet1809/WellQuery)"

class Source(BaseModel):
    """Explicit source attribution and permission record."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1)
    publisher: str = Field(min_length=1)
    url: HttpUrl
    licence: str = Field(min_length=1)
    licence_url: HttpUrl
    permission_checked_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    approved: bool
    category: Literal["drug", "condition", "all"]
    format: Literal["html", "txt"] = "html"
    selector: str = Field(default="main", min_length=1)


def load_catalogue(path: Path) -> list[Source]:
    """Reject duplicates and sources not yet approved for ingestion."""
    sources = [Source.model_validate(item) for item in json.loads(path.read_text())]
    if not sources or len({s.id for s in sources}) != len(sources):
        raise ValueError("Catalogue must be nonempty with unique source IDs")
    if any(not s.approved for s in sources):
        raise ValueError("All sources must have reviewed reuse permissions")
    return sources


def extract_sections(raw: str, source: Source) -> list[tuple[str, str]]:
    """Extract only the selected article; preserve section labels and exclude media."""
    if source.format == "txt":
        return [(source.title, raw.strip())] if raw.strip() else []
    soup = BeautifulSoup(raw, "html.parser")
    article = soup.select_one(source.selector)
    if article is None:
        raise ValueError(f"Article selector not found for {source.id}")
    for node in article.select("script, style, nav, header, footer, aside, figure, img, form, table, .share"):
        node.decompose()
    sections = []
    headings: dict[int, str] = {}
    paragraphs: list[str] = []
    heading = source.title
    for node in article.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        if node.name == "p" and node.find_parent("li"):
            continue
        if node.name == "li" and node.find_parent("li"):
            continue
        text = " ".join(node.get_text(" ", strip=True).split())
        if not text:
            continue
        if node.name.startswith("h"):
            if paragraphs:
                sections.append((heading, "\n".join(paragraphs)))
            paragraphs = []
            level = int(node.name[1])
            headings = {k: v for k, v in headings.items() if k < level}
            headings[level] = text
            heading = " > ".join(headings.values())
        else:
            paragraphs.append(text)
    if paragraphs:
        sections.append((heading, "\n".join(paragraphs)))
    return sections


def chunk_sections(sections: list[tuple[str, str]], max_words: int = 180, overlap: int = 30):
    """Produce bounded word windows without crossing section boundaries."""
    if max_words < 1 or not 0 <= overlap < max_words:
        raise ValueError("Require max_words > overlap >= 0")
    for heading, text in sections:
        words = text.split()
        for start in range(0, len(words), max_words - overlap):
            yield heading, " ".join(words[start:start + max_words])
            if start + max_words >= len(words):
                break


class Downloader:
    """Explicit downloads with robots checks, timeouts, size limits, and host pacing."""
    def __init__(self):
        self.last: dict[str, float] = {}
        self.robots: dict[str, RobotFileParser] = {}

    def read(self, url: str) -> bytes:
        """Read a small response; reject redirects rather than fetching unchecked hosts."""
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.username or parsed.password:
            raise ValueError("Only HTTPS sources without URL credentials are supported")
        host = parsed.netloc
        time.sleep(max(0, 1 - (time.monotonic() - self.last.get(host, 0))))
        self.last[host] = time.monotonic()
        with requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30,
                          stream=True, allow_redirects=False) as response:
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError("Source redirects or unexpected status; update the catalogue")
            body = bytearray()
            for part in response.iter_content(65536):
                body.extend(part)
                if len(body) > 3_000_000:
                    raise ValueError("Source exceeds 3 MB limit")
            return bytes(body)

    def fetch(self, source: Source) -> bytes:
        """Check robots before accessing a catalogue URL."""
        url = str(source.url)
        parsed = urlsplit(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self.robots:
            parser = RobotFileParser()
            parser.parse(self.read(origin + "/robots.txt").decode("utf-8").splitlines())
            self.robots[origin] = parser
        if not self.robots[origin].can_fetch(USER_AGENT, url):
            raise ValueError(f"robots.txt disallows {source.id}")
        return self.read(url)


def ingest(catalogue: Path, raw_dir: Path, database: Path, *, download: bool = False,
           refresh: bool = False, max_words: int = 180, overlap: int = 30) -> dict:
    """Validate and prepare the whole catalogue before atomically replacing documents."""
    if refresh and not download:
        raise ValueError("Refresh requires explicit download permission via --download")
    sources = load_catalogue(catalogue)
    raw_dir.mkdir(parents=True, exist_ok=True)
    downloader = Downloader()
    prepared = []
    for source in sources:
        raw_path = raw_dir / f"{source.id}.{source.format}"
        receipt_path = raw_dir / f"{source.id}.receipt.json"
        if refresh or not raw_path.exists():
            if not download:
                raise ValueError(f"Missing cached source {source.id}; use --download")
            raw = downloader.fetch(source)
            raw_path.write_bytes(raw)
            receipt_path.write_text(json.dumps({"url": str(source.url), "retrieved_at": datetime.now(timezone.utc).isoformat(),
                                               "sha256": hashlib.sha256(raw).hexdigest()}))
        raw = raw_path.read_bytes()
        raw_hash = hashlib.sha256(raw).hexdigest()
        retrieved_at = None
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            if receipt["sha256"] != raw_hash or receipt["url"] != str(source.url):
                raise ValueError(f"Cached source metadata mismatch for {source.id}; refresh it")
            retrieved_at = receipt["retrieved_at"]
        chunks = list(chunk_sections(extract_sections(raw.decode("utf-8"), source), max_words, overlap))
        if not chunks:
            raise ValueError(f"No article text for {source.id}")
        metadata = source.model_dump(mode="json")
        metadata.update(retrieved_at=retrieved_at, content_sha256=raw_hash,
                        chunk_max_words=max_words, chunk_overlap=overlap, parser_version=1)
        fingerprint = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
        prepared.append((source, metadata, fingerprint, chunks))
    database.parent.mkdir(parents=True, exist_ok=True)
    changed = 0
    with sqlite3.connect(database) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, metadata TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS chunks (id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE, section_path TEXT NOT NULL, chunk_index INTEGER NOT NULL, chunk_text TEXT NOT NULL)")
        for source, metadata, fingerprint, chunks in prepared:
            previous = conn.execute("SELECT fingerprint FROM documents WHERE id=?", (source.id,)).fetchone()
            if previous and previous[0] == fingerprint:
                continue
            conn.execute("DELETE FROM documents WHERE id=?", (source.id,))
            conn.execute("INSERT INTO documents VALUES (?, ?, ?)", (source.id, fingerprint, json.dumps(metadata)))
            conn.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?, ?)", [
                (f"{source.id}:{i}", source.id, heading, i, text) for i, (heading, text) in enumerate(chunks)])
            changed += 1
        count = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
    return {"sources_processed": len(sources), "documents_changed": changed, "total_chunks": count}


def main():
    """CLI for explicit source ingestion; network access is opt-in."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=Path("data/sources.json"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--database", type=Path, default=Path("data/processed/wellquery.sqlite3"))
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    try:
        result = ingest(args.catalogue, args.raw_dir, args.database, download=args.download, refresh=args.refresh)
    except (ValueError, OSError, requests.RequestException) as exc:
        parser.exit(1, f"Ingestion failed: {exc}\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
