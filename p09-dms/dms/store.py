"""One SQLite database and one content-addressed file store per region."""
import hashlib
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, title TEXT, doc_type TEXT, entity TEXT, region TEXT, dept TEXT,
  language TEXT, classification TEXT, status TEXT, owner TEXT, tags TEXT,
  current_version INTEGER, created_utc TEXT, updated_utc TEXT,
  retention_until TEXT, legal_hold INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS versions (
  doc_id TEXT, version INTEGER, sha256 TEXT, filename TEXT, size INTEGER,
  author TEXT, note TEXT, created_utc TEXT, PRIMARY KEY (doc_id, version));
CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
  doc_id UNINDEXED, title, body, tags, tokenize = 'unicode61 remove_diacritics 2');
CREATE TABLE IF NOT EXISTS audit (
  ts_utc TEXT, actor TEXT, action TEXT, doc_id TEXT, detail TEXT);
"""


def now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class RegionStore:
    def __init__(self, root: Path, region: str):
        self.region = region
        self.dir = Path(root) / region
        self.blobs = self.dir / "blobs"
        self.blobs.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False: the web API serves requests from a thread pool
        self.db = sqlite3.connect(self.dir / "dms.sqlite", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def put_blob(self, src: Path) -> tuple[str, int]:
        """Content-addressed: the file's SHA-256 is its storage name, so duplicates cost nothing
        and any tampering is detectable."""
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        dest = self.blobs / digest[:2] / digest
        if not dest.exists():
            dest.parent.mkdir(exist_ok=True)
            shutil.copy2(src, dest)
        return digest, dest.stat().st_size

    def blob_path(self, digest: str) -> Path:
        return self.blobs / digest[:2] / digest

    def audit(self, actor: str, action: str, doc_id: str, detail: str = "") -> None:
        self.db.execute("INSERT INTO audit VALUES (?,?,?,?,?)", (now_utc(), actor, action, doc_id, detail))

    def next_id(self) -> str:
        n = self.db.execute("SELECT COUNT(*) FROM documents").fetchone()[0] + 1
        return f"{self.region.upper()}-{n:06d}"
