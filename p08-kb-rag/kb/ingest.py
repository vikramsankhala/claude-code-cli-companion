"""Ingestion: read documents, split them into chunks, embed and index them."""
import hashlib
from pathlib import Path

from . import store

MAX_CHARS = 900


def chunk_markdown(text: str, title: str) -> list[str]:
    """Split on blank lines, pack paragraphs up to MAX_CHARS, and prefix each chunk
    with 'Title > Section' so every chunk still makes sense on its own."""
    chunks, buf, section = [], [], ""

    def flush():
        if buf:
            head = f"{title} > {section}" if section and section != title else title
            chunks.append(head + "\n\n" + "\n\n".join(buf))

    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        if para.startswith("#"):
            flush()
            buf = []
            section = para.lstrip("#").strip()
            continue
        if buf and len("\n\n".join(buf)) + len(para) > MAX_CHARS:
            flush()
            buf = buf[-1:]  # overlap: carry the last paragraph into the next chunk
        buf.append(para)
    flush()
    return chunks


def ingest(root: str, db, embedder) -> dict:
    """Incremental: unchanged files are skipped, changed files re-indexed, deleted files removed."""
    root_path = Path(root)
    seen, stats = set(), {"added": 0, "updated": 0, "skipped": 0, "removed": 0, "chunks": 0}
    for path in sorted(root_path.rglob("*")):
        if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
            continue
        rel = path.relative_to(root_path).as_posix()        # forward slashes on Windows too
        seen.add(rel)
        text = path.read_text(encoding="utf-8", errors="replace")
        digest = hashlib.sha256(text.encode()).hexdigest()
        old = db.execute("SELECT hash FROM docs WHERE path = ?", (rel,)).fetchone()
        if old and old[0] == digest:
            stats["skipped"] += 1
            continue
        if old:
            store.delete_doc(db, rel)
        dept = rel.rsplit("/", 1)[0] if "/" in rel else "general"  # folder = access group, e.g. in/hr
        first = text.lstrip().splitlines()[0] if text.strip() else rel
        title = first.lstrip("# ").strip() if first.startswith("#") else path.stem
        pieces = chunk_markdown(text, title)
        vecs = embedder.embed(pieces) if pieces else []
        for piece, vec in zip(pieces, vecs):
            store.add_chunk(db, rel, title, dept, piece, vec)
        db.execute("INSERT OR REPLACE INTO docs(path, hash) VALUES (?, ?)", (rel, digest))
        stats["updated" if old else "added"] += 1
        stats["chunks"] += len(pieces)
    for (rel,) in db.execute("SELECT path FROM docs").fetchall():
        if rel not in seen:
            store.delete_doc(db, rel)
            stats["removed"] += 1
    db.execute("INSERT OR REPLACE INTO meta VALUES ('embedder', ?)", (embedder.name,))
    db.commit()
    return stats
