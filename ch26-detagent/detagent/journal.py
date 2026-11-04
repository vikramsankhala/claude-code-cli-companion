"""Append-only, hash-chained journal: every entry commits to the one before, so edits show."""
import hashlib
import json
import sqlite3

GENESIS = "0" * 64


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class Journal:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS journal(seq INTEGER PRIMARY KEY, run_id TEXT, step TEXT,"
                        " payload TEXT, prev TEXT, hash TEXT)")

    def head(self) -> str:
        r = self.db.execute("SELECT hash FROM journal ORDER BY seq DESC LIMIT 1").fetchone()
        return r[0] if r else GENESIS

    def append(self, run_id: str, step: str, payload: dict) -> str:
        prev = self.head()
        body = canon({"run_id": run_id, "step": step, "payload": payload, "prev": prev})
        h = hashlib.sha256(body.encode()).hexdigest()
        self.db.execute("INSERT INTO journal(run_id, step, payload, prev, hash) VALUES (?,?,?,?,?)",
                        (run_id, step, canon(payload), prev, h))
        self.db.commit()
        return h

    def verify(self) -> int | None:
        """Return the seq of the first broken entry, or None if the chain is intact."""
        prev = GENESIS
        for seq, run_id, step, payload, p, h in self.db.execute("SELECT * FROM journal ORDER BY seq"):
            body = canon({"run_id": run_id, "step": step, "payload": json.loads(payload), "prev": prev})
            if p != prev or hashlib.sha256(body.encode()).hexdigest() != h:
                return seq
            prev = h
        return None

    def steps(self, run_id: str) -> list[str]:
        return [r[0] for r in self.db.execute("SELECT step FROM journal WHERE run_id=? ORDER BY seq", (run_id,))]
