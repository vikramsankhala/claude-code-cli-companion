"""A durable job queue in SQLite: every automated step is a job that can retry and be audited."""
import json
import sqlite3
from datetime import UTC, datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, kind TEXT, payload TEXT,
  status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0, error TEXT, created_utc TEXT, done_utc TEXT);
CREATE TABLE IF NOT EXISTS notifications (ts_utc TEXT, recipient TEXT, subject TEXT, body TEXT);
CREATE TABLE IF NOT EXISTS seen_files (path TEXT PRIMARY KEY, sha256 TEXT);
CREATE TABLE IF NOT EXISTS query_log (ts_utc TEXT, user TEXT, query TEXT, results INTEGER);
CREATE TABLE IF NOT EXISTS published (doc_id TEXT PRIMARY KEY, version INTEGER, region TEXT);
CREATE TABLE IF NOT EXISTS sync_state (source TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS external_items (source TEXT, ext_id TEXT, doc_id TEXT, sha256 TEXT,
  PRIMARY KEY (source, ext_id));
"""
MAX_ATTEMPTS = 3


def now():
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class Queue:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def put(self, kind: str, **payload) -> None:
        self.db.execute("INSERT INTO jobs(kind, payload, created_utc) VALUES (?,?,?)",
                        (kind, json.dumps(payload), now()))
        self.db.commit()

    def take(self):
        row = self.db.execute("SELECT * FROM jobs WHERE status='pending' ORDER BY id LIMIT 1").fetchone()
        if row:
            self.db.execute("UPDATE jobs SET status='running', attempts=attempts+1 WHERE id=?", (row["id"],))
            self.db.commit()
        return row

    def done(self, job_id: int) -> None:
        self.db.execute("UPDATE jobs SET status='done', done_utc=? WHERE id=?", (now(), job_id))
        self.db.commit()

    def fail(self, job, error: str) -> None:
        status = "failed" if job["attempts"] + 1 >= MAX_ATTEMPTS else "pending"  # retry, then park
        self.db.execute("UPDATE jobs SET status=?, error=? WHERE id=?", (status, error[:500], job["id"]))
        self.db.commit()

    def notify(self, recipient, subject, body) -> None:
        """Stand-in for email, Teams or Slack: replace with your messaging connector."""
        self.db.execute("INSERT INTO notifications VALUES (?,?,?,?)", (now(), recipient, subject, body))
        self.db.commit()
