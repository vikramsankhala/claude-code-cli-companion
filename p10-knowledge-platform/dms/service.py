"""Document lifecycle: register, version, approve, retrieve, search, retain, audit."""
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import CLASSIFICATION, DEFAULT_RETENTION_YEARS, REGIONS, RETENTION_YEARS, STATUSES
from .extract import extract_text
from .query import parse
from .store import RegionStore, now_utc


class AccessDenied(Exception):
    pass


class User:
    """regions: where this person may read; depts: ['*'] for all; max_class: highest level."""

    def __init__(self, name, regions, depts=("*",), max_class="internal", can_approve=False):
        self.name, self.regions, self.depts = name, list(regions), list(depts)
        self.max_class, self.can_approve = max_class, can_approve

    def may_read(self, row) -> bool:
        return (row["region"] in self.regions
                and ("*" in self.depts or row["dept"] in self.depts)
                and CLASSIFICATION.index(row["classification"]) <= CLASSIFICATION.index(self.max_class))


def load_users(path) -> dict:
    return {n: User(n, **cfg) for n, cfg in json.loads(Path(path).read_text()).items()}


class DMS:
    def __init__(self, root):
        self.stores = {r: RegionStore(Path(root), r) for r in REGIONS}

    # ------------------------------------------------------------------ write
    def register(self, user, file, *, title, doc_type, entity, region, dept, language,
                 classification="internal", tags=(), note="initial version") -> str:
        if region not in self.stores:
            raise ValueError(f"Unknown region {region!r}; choose from {sorted(REGIONS)}")
        if classification not in CLASSIFICATION:
            raise ValueError(f"classification must be one of {CLASSIFICATION}")
        s = self.stores[region]
        doc_id, ts = s.next_id(), now_utc()
        s.db.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
                     (doc_id, title, doc_type, entity, region, dept, language, classification, "draft",
                      user.name, ",".join(tags), 0, ts, ts, None))
        self._add_version(s, user, doc_id, Path(file), note)
        s.audit(user.name, "register", doc_id, f"{doc_type} in {region}")
        s.db.commit()
        return doc_id

    def add_version(self, user, doc_id, file, note="") -> int:
        s, row = self._row(user, doc_id)
        if row["status"] == "archived":
            raise ValueError("Archived documents are read-only")
        v = self._add_version(s, user, doc_id, Path(file), note)
        if row["status"] != "draft":  # changed content must be reviewed again
            s.db.execute("UPDATE documents SET status='draft' WHERE id=?", (doc_id,))
        s.audit(user.name, "new_version", doc_id, f"v{v}: {note}")
        s.db.commit()
        return v

    def _add_version(self, s, user, doc_id, file, note) -> int:
        digest, size = s.put_blob(file)
        v = s.db.execute("SELECT COALESCE(MAX(version),0)+1 FROM versions WHERE doc_id=?", (doc_id,)).fetchone()[0]
        ts = now_utc()
        s.db.execute("INSERT INTO versions VALUES (?,?,?,?,?,?,?,?)",
                     (doc_id, v, digest, file.name, size, user.name, note, ts))
        row = s.db.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        years = RETENTION_YEARS.get((row["region"], row["doc_type"]), DEFAULT_RETENTION_YEARS)
        until = (datetime.now(timezone.utc) + timedelta(days=365 * years)).strftime("%Y-%m-%d")
        s.db.execute("UPDATE documents SET current_version=?, updated_utc=?, retention_until=? WHERE id=?",
                     (v, ts, until, doc_id))
        # the search index always holds the current version only
        s.db.execute("DELETE FROM search_index WHERE doc_id=?", (doc_id,))
        s.db.execute("INSERT INTO search_index(doc_id, title, body, tags) VALUES (?,?,?,?)",
                     (doc_id, row["title"], extract_text(file), row["tags"]))
        return v

    def set_status(self, user, doc_id, new) -> None:
        s, row = self._row(user, doc_id)
        if new not in STATUSES[row["status"]]:
            raise ValueError(f"Cannot move {row['status']} -> {new}")
        if new == "approved" and not user.can_approve:
            raise AccessDenied(f"{user.name} cannot approve documents")
        s.db.execute("UPDATE documents SET status=?, updated_utc=? WHERE id=?", (new, now_utc(), doc_id))
        s.audit(user.name, "status", doc_id, f"{row['status']} -> {new}")
        s.db.commit()

    def set_legal_hold(self, user, doc_id, on: bool) -> None:
        s, _ = self._row(user, doc_id)
        s.db.execute("UPDATE documents SET legal_hold=? WHERE id=?", (int(on), doc_id))
        s.audit(user.name, "legal_hold", doc_id, "on" if on else "off")
        s.db.commit()

    def purge_expired(self, actor="retention-job", today=None) -> list[str]:
        """Delete documents past retention, except those under legal hold."""
        today = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        purged = []
        for s in self.stores.values():
            for row in s.db.execute("SELECT id FROM documents WHERE retention_until < ? AND legal_hold = 0",
                                    (today,)).fetchall():
                for (digest,) in s.db.execute("SELECT sha256 FROM versions WHERE doc_id=?", (row["id"],)).fetchall():
                    in_use = s.db.execute("SELECT COUNT(*) FROM versions WHERE sha256=? AND doc_id<>?",
                                          (digest, row["id"])).fetchone()[0]
                    if not in_use:
                        s.blob_path(digest).unlink(missing_ok=True)
                for table, col in (("versions", "doc_id"), ("search_index", "doc_id"), ("documents", "id")):
                    s.db.execute(f"DELETE FROM {table} WHERE {col}=?", (row["id"],))
                s.audit(actor, "purge", row["id"], "retention expired")
                purged.append(row["id"])
            s.db.commit()
        return purged

    # ------------------------------------------------------------------ read
    def _row(self, user, doc_id):
        region = doc_id.split("-")[0].lower()
        s = self.stores.get(region)
        row = s and s.db.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        if not row:
            raise KeyError(doc_id)
        if not user.may_read(row):
            s.audit(user.name, "denied", doc_id, "")
            s.db.commit()
            raise AccessDenied(f"{user.name} may not access {doc_id}")
        return s, row

    def get(self, user, doc_id, version=None, dest=None) -> dict:
        s, row = self._row(user, doc_id)
        v = version or row["current_version"]
        ver = s.db.execute("SELECT * FROM versions WHERE doc_id=? AND version=?", (doc_id, v)).fetchone()
        if not ver:
            raise KeyError(f"{doc_id} v{v}")
        out = None
        if dest:
            out = Path(dest) / ver["filename"]
            shutil.copy2(s.blob_path(ver["sha256"]), out)
        s.audit(user.name, "retrieve", doc_id, f"v{v}")
        s.db.commit()
        return {**dict(row), "version": v, "sha256": ver["sha256"], "filename": ver["filename"],
                "path": str(out) if out else str(s.blob_path(ver["sha256"]))}

    def history(self, user, doc_id) -> list[dict]:
        s, _ = self._row(user, doc_id)
        return [dict(r) for r in s.db.execute(
            "SELECT version, filename, author, note, created_utc FROM versions WHERE doc_id=? ORDER BY version",
            (doc_id,))]

    def search(self, user, query: str, limit: int = 20) -> list[dict]:
        """Federated: runs in every region the user may read, then merges by relevance."""
        words, filters = parse(query)
        results = []
        for region in user.regions:
            s = self.stores.get(region)
            if not s:
                continue
            where, args = ["1=1"], []
            for col, op, val in filters:
                if col == "tags":
                    where.append("(',' || d.tags || ',') LIKE ?")
                    args.append(f"%,{val},%")
                else:
                    where.append(f"d.{col} {op} ?")
                    args.append(val)
            if words:
                match = " ".join(f'"{w}"' for w in words)
                sql = (f"SELECT d.*, bm25(search_index) AS rank, snippet(search_index, 2, '[', ']', ' … ', 12) AS snip "
                       f"FROM search_index JOIN documents d ON d.id = search_index.doc_id "
                       f"WHERE search_index MATCH ? AND {' AND '.join(where)} ORDER BY rank LIMIT ?")
                rows = s.db.execute(sql, [match, *args, limit]).fetchall()
            else:
                sql = (f"SELECT d.*, 0 AS rank, '' AS snip FROM documents d WHERE {' AND '.join(where)} "
                       f"ORDER BY d.updated_utc DESC LIMIT ?")
                rows = s.db.execute(sql, [*args, limit]).fetchall()
            results += [dict(r) for r in rows if user.may_read(r)]
            s.audit(user.name, "search", "", query)
            s.db.commit()
        return sorted(results, key=lambda r: r["rank"])[:limit]

    def audit_log(self, region, limit=50) -> list[dict]:
        return [dict(r) for r in self.stores[region].db.execute(
            "SELECT * FROM audit ORDER BY rowid DESC LIMIT ?", (limit,))]
