"""Storage: one SQLite file holds chunks, a keyword index (FTS5) and vectors."""
import os
import sqlite3

import numpy as np

from .embed import tokens

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs   (path TEXT PRIMARY KEY, hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY, doc TEXT, title TEXT,
                                   dept TEXT, text TEXT, vec BLOB);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text, title,
    tokenize = 'unicode61 remove_diacritics 2');  -- matches 'resume' and 'résumé' alike
CREATE TABLE IF NOT EXISTS meta   (key TEXT PRIMARY KEY, value TEXT);
"""


def connect(path: str = "kb.sqlite") -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    return db


def add_chunk(db, doc, title, dept, text, vec: np.ndarray) -> None:
    cur = db.execute("INSERT INTO chunks(doc, title, dept, text, vec) VALUES (?,?,?,?,?)",
                     (doc, title, dept, text, vec.astype(np.float32).tobytes()))
    db.execute("INSERT INTO chunks_fts(rowid, text, title) VALUES (?,?,?)", (cur.lastrowid, text, title))


def delete_doc(db, doc) -> None:
    ids = [r[0] for r in db.execute("SELECT id FROM chunks WHERE doc = ?", (doc,))]
    db.executemany("DELETE FROM chunks_fts WHERE rowid = ?", [(i,) for i in ids])
    db.execute("DELETE FROM chunks WHERE doc = ?", (doc,))
    db.execute("DELETE FROM docs WHERE path = ?", (doc,))


def _dept_filter(groups):
    """Access groups are folder paths such as 'in/hr' or 'global'. Allowing 'in'
    also allows everything under it ('in/hr', 'in/finance')."""
    if not groups:
        return "0", []
    parts, args = [], []
    for g in groups:
        parts.append("(c.dept = ? OR c.dept LIKE ?)")
        args += [g, g.rstrip("/") + "/%"]
    return "(" + " OR ".join(parts) + ")", args


def keyword_search(db, query, depts, k=20) -> list[int]:
    """BM25 ranking from SQLite FTS5. Each word is quoted so user text can't break the syntax."""
    words = [w for w in tokens(query) if len(w) > 2]
    if not words:
        return []
    match = " OR ".join(f'"{w}"' for w in words)
    where, args = _dept_filter(depts)
    rows = db.execute(
        f"SELECT c.id FROM chunks_fts f JOIN chunks c ON c.id = f.rowid "
        f"WHERE chunks_fts MATCH ? AND {where} ORDER BY bm25(chunks_fts) LIMIT ?",
        [match, *args, k]).fetchall()
    return [r[0] for r in rows]


def vector_search(db, qvec: np.ndarray, depts, k=20, min_sim=None) -> list[int]:
    """Cosine similarity by brute force: fine to ~100k chunks; use a vector DB beyond.
    Hits below min_sim are dropped, so unrelated questions return nothing (tune per model)."""
    min_sim = float(os.getenv("KB_MIN_SIM", "0.15")) if min_sim is None else min_sim
    where, args = _dept_filter(depts)
    rows = db.execute(f"SELECT c.id, c.vec FROM chunks c WHERE {where}", args).fetchall()
    if not rows:
        return []
    ids = [r[0] for r in rows]
    matrix = np.frombuffer(b"".join(r[1] for r in rows), dtype=np.float32).reshape(len(rows), -1)
    scores = matrix @ qvec.astype(np.float32)
    return [ids[i] for i in np.argsort(-scores)[:k] if scores[i] >= min_sim]


def get_chunks(db, ids) -> dict:
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    rows = db.execute(f"SELECT id, doc, title, dept, text FROM chunks WHERE id IN ({marks})", ids)
    return {r[0]: {"id": r[0], "doc": r[1], "title": r[2], "dept": r[3], "text": r[4]} for r in rows}
