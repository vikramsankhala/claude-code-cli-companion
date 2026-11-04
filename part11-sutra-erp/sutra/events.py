"""Event store: every business fact is an immutable, hash-chained event. Tables are views of events."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone

GENESIS = "0" * 64
SCHEMA = """
CREATE TABLE IF NOT EXISTS events(
  seq INTEGER PRIMARY KEY, tenant TEXT NOT NULL, stream TEXT NOT NULL, type TEXT NOT NULL,
  actor TEXT NOT NULL, actor_kind TEXT NOT NULL CHECK(actor_kind IN ('human','agent','system','device')),
  at TEXT NOT NULL, payload TEXT NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL UNIQUE);
CREATE INDEX IF NOT EXISTS ev_stream ON events(tenant, stream);
CREATE INDEX IF NOT EXISTS ev_type ON events(tenant, type);
CREATE TRIGGER IF NOT EXISTS ev_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS ev_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
"""


def canon(o) -> str:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class EventStore:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(SCHEMA)

    def head(self) -> str:
        r = self.db.execute("SELECT hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        return r[0] if r else GENESIS

    def append(self, tenant, stream, type_, payload, actor="system", actor_kind="system", at=None) -> dict:
        ev = {"tenant": tenant, "stream": stream, "type": type_, "actor": actor, "actor_kind": actor_kind,
              "at": at or utcnow(), "payload": payload, "prev": self.head()}
        ev["hash"] = hashlib.sha256(canon(ev).encode()).hexdigest()
        cur = self.db.execute("INSERT INTO events(tenant,stream,type,actor,actor_kind,at,payload,prev,hash) "
                              "VALUES (?,?,?,?,?,?,?,?,?)", (tenant, stream, type_, actor, actor_kind, ev["at"],
                                                             canon(payload), ev["prev"], ev["hash"]))
        self.db.commit()
        ev["seq"] = cur.lastrowid
        return ev

    def read(self, tenant=None, type_=None, stream=None):
        q, a = "SELECT seq,tenant,stream,type,actor,actor_kind,at,payload,prev,hash FROM events WHERE 1=1", []
        for col, v in (("tenant", tenant), ("type", type_), ("stream", stream)):
            if v is not None:
                q += f" AND {col}=?"
                a.append(v)
        for r in self.db.execute(q + " ORDER BY seq", a):
            yield dict(zip(("seq", "tenant", "stream", "type", "actor", "actor_kind", "at", "payload", "prev", "hash"),
                           r[:7] + (json.loads(r[7]),) + r[8:]))

    def verify(self) -> int | None:
        """First seq whose hash or link is wrong, or None when the whole chain is intact."""
        prev = GENESIS
        for e in self.read():
            body = {k: e[k] for k in ("tenant", "stream", "type", "actor", "actor_kind", "at", "payload")}
            body["prev"] = prev
            if e["prev"] != prev or hashlib.sha256(canon(body).encode()).hexdigest() != e["hash"]:
                return e["seq"]
            prev = e["hash"]
        return None
