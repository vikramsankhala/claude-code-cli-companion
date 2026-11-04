"""The platform: wires the DMS, the regional knowledge indexes and the automation pipeline.

Flow (every arrow is a queued job):
  inbox file -> ingest (classify + register, status review) -> notify reviewers
  approval   -> publish (index current version for RAG)
  new version / archive / purge -> unpublish
  nightly    -> reconcile, retention, evaluation, knowledge-gap report
"""
import hashlib
import json
import os
import traceback
from pathlib import Path

from dms.config import CLASSIFICATION, REGIONS
from dms.extract import extract_text
from dms.service import DMS, User, load_users
from kb import store as kbstore
from kb.answer import SYSTEM, build_prompt
from kb.embed import get_embedder
from kb.ingest import index_text
from kb.search import hybrid_search

from . import connectors
from .classify import classify
from .queue import Queue, now

BOT = User("automation", regions=list(REGIONS), max_class="restricted", can_approve=False)
ENTITIES = {"in": "Acme India Pvt Ltd", "eu": "Acme GmbH", "us": "Acme Inc"}  # sample legal entities


class Platform:
    def __init__(self, root, users_file="users.json"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.dms = DMS(self.root / "stores")
        self.users = load_users(users_file)
        self.q = Queue(self.root / "platform.sqlite")
        self.emb = get_embedder()
        self.kb = {r: kbstore.connect(str(self.root / "stores" / r / "kb.sqlite")) for r in REGIONS}
        self.inbox = self.root / "inbox"
        for r in REGIONS:
            (self.inbox / r).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------ triggers
    def scan_inbox(self) -> int:
        """inbox/<region>/<dept>/<file>: new or changed files become ingest jobs."""
        n = 0
        for f in sorted(self.inbox.rglob("*")):
            if not f.is_file() or len(f.relative_to(self.inbox).parts) != 3:
                continue
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            key = str(f.relative_to(self.inbox))
            row = self.q.db.execute("SELECT sha256 FROM seen_files WHERE path=?", (key,)).fetchone()
            if row and row[0] == digest:
                continue
            self.q.db.execute("INSERT OR REPLACE INTO seen_files VALUES (?,?)", (key, digest))
            self.q.put("ingest", path=key)
            n += 1
        self.q.db.commit()
        return n

    def load_sources(self, path="sources.json") -> list[dict]:
        p = Path(path)
        return json.loads(p.read_text()) if p.exists() else []

    def sync_sources(self, sources: list[dict]) -> None:
        """Queue one sync job per external source (run on a schedule)."""
        for cfg in sources:
            self.q.put("sync_source", cfg=cfg)

    def approve(self, user, doc_id) -> None:
        self.dms.set_status(user, doc_id, "approved")
        self.q.put("publish", doc_id=doc_id)

    def archive(self, user, doc_id) -> None:
        self.dms.set_status(user, doc_id, "archived")
        self.q.put("unpublish", doc_id=doc_id)

    def nightly(self) -> None:
        self.sync_sources(self.load_sources(os.getenv("KMP_SOURCES", "sources.json")))
        for kind in ("reconcile", "retention", "gap_report"):
            self.q.put(kind)

    # ------------------------------------------------------------ worker
    def run(self, max_jobs=1000) -> int:
        handled = 0
        while handled < max_jobs and (job := self.q.take()):
            try:
                getattr(self, f"_job_{job['kind']}")(**json.loads(job["payload"]))
                self.q.done(job["id"])
            except Exception as e:  # keep the worker alive; the job retries or parks as failed
                self.q.fail(job, f"{type(e).__name__}: {e}\n{traceback.format_exc(limit=2)}")
            handled += 1
        return handled

    def _job_ingest(self, path):
        f = self.inbox / path
        region, dept, _ = Path(path).parts
        text = extract_text(f)
        meta = classify(text, f.name)
        existing = self.dms.search(BOT, f'region:{region} dept:{dept} "{meta["title"]}"', limit=1)
        if existing and existing[0]["title"] == meta["title"]:
            doc_id = existing[0]["id"]
            self.dms.add_version(BOT, doc_id, f, "auto: inbox update")
            self.q.put("unpublish", doc_id=doc_id)  # old version leaves the index until re-approved
        else:
            doc_id = self.dms.register(BOT, f, title=meta["title"], doc_type=meta["doc_type"],
                                       entity=ENTITIES.get(region, region), region=region, dept=dept,
                                       language=meta["language"], classification=meta["classification"],
                                       tags=meta["tags"], note="auto-ingested from inbox")
        self.dms.set_status(BOT, doc_id, "review")
        self.q.put("notify_review", doc_id=doc_id)

    def _job_sync_source(self, cfg):
        """Incremental pull: only records changed since the last watermark."""
        db = self.q.db
        state = db.execute("SELECT value FROM sync_state WHERE source=?", (cfg["name"],)).fetchone()
        since = state[0] if state else ""
        newest = since
        for item in connectors.build(cfg).fetch(since):
            self._ingest_item(cfg, item)
            newest = max(newest, item.updated)
        db.execute("INSERT OR REPLACE INTO sync_state VALUES (?,?)", (cfg["name"], newest))
        db.commit()

    def _ingest_item(self, cfg, item):
        import tempfile
        text = f"# {item.title}\n\n{item.body}\n\nSource: {cfg['name']} · {item.url or item.ext_id}\n"
        digest = hashlib.sha256(text.encode()).hexdigest()
        row = self.q.db.execute("SELECT doc_id, sha256 FROM external_items WHERE source=? AND ext_id=?",
                                (cfg["name"], item.ext_id)).fetchone()
        if row and row["sha256"] == digest:
            return
        meta = classify(text, item.title)
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / f"{cfg['name']}-{item.ext_id}.md"
            f.write_text(text, encoding="utf-8")
            if row:
                doc_id = row["doc_id"]
                self.dms.add_version(BOT, doc_id, f, f"sync from {cfg['name']}")
                self.q.put("unpublish", doc_id=doc_id)
            else:
                doc_id = self.dms.register(
                    BOT, f, title=item.title, doc_type=cfg.get("doc_type", meta["doc_type"]),
                    entity=ENTITIES.get(cfg["region"], cfg["region"]), region=cfg["region"], dept=cfg["dept"],
                    language=meta["language"], classification=cfg.get("classification", meta["classification"]),
                    tags=meta["tags"] + [f"source:{cfg['name']}"], note=f"imported from {cfg['name']}")
        self.q.db.execute("INSERT OR REPLACE INTO external_items VALUES (?,?,?,?)",
                          (cfg["name"], item.ext_id, doc_id, digest))
        if cfg.get("auto_approve"):   # trusted, already-governed sources skip human review
            self.dms.set_status(BOT, doc_id, "review")
            self.dms.set_status(_approver(), doc_id, "approved")
            self.q.put("publish", doc_id=doc_id)
        else:
            self.dms.set_status(BOT, doc_id, "review")
            self.q.put("notify_review", doc_id=doc_id)

    def _job_notify_review(self, doc_id):
        d = self.dms.get(BOT, doc_id)
        for u in self.users.values():
            if u.can_approve and u.may_read(d):
                self.q.notify(u.name, f"Review needed: {doc_id}",
                              f"{d['title']} ({d['doc_type']}, {d['language']}, {d['classification']})")

    def _job_publish(self, doc_id):
        d = self.dms.get(BOT, doc_id)
        if d["status"] != "approved":
            return
        group = f"{d['region']}/{d['classification']}/{d['dept']}"
        key = f"{doc_id}@v{d['version']}"
        db = self.kb[d["region"]]
        for (old,) in db.execute("SELECT path FROM docs WHERE path LIKE ?", (f"{doc_id}@%",)).fetchall():
            kbstore.remove_key(db, old)
        index_text(db, self.emb, key, d["title"], group, _read_blob_text(d))
        self.q.db.execute("INSERT OR REPLACE INTO published VALUES (?,?,?)", (doc_id, d["version"], d["region"]))
        self.q.db.commit()

    def _job_unpublish(self, doc_id):
        region = doc_id.split("-")[0].lower()
        db = self.kb[region]
        for (key,) in db.execute("SELECT path FROM docs WHERE path LIKE ?", (f"{doc_id}@%",)).fetchall():
            kbstore.remove_key(db, key)
        db.commit()
        self.q.db.execute("DELETE FROM published WHERE doc_id=?", (doc_id,))
        self.q.db.commit()

    def _job_reconcile(self):
        """Self-healing: the index must hold exactly the approved, current versions."""
        approved = {d["id"]: d["current_version"] for d in self.dms.search(BOT, "status:approved", limit=100000)}
        published = {r[0]: r[1] for r in self.q.db.execute("SELECT doc_id, version FROM published")}
        for doc_id, v in approved.items():
            if published.get(doc_id) != v:
                self.q.put("publish", doc_id=doc_id)
        for doc_id in published.keys() - approved.keys():
            self.q.put("unpublish", doc_id=doc_id)

    def _job_retention(self):
        for doc_id in self.dms.purge_expired():
            self.q.put("unpublish", doc_id=doc_id)

    def _job_gap_report(self):
        rows = self.q.db.execute("SELECT query, COUNT(*) n FROM query_log WHERE results = 0 "
                                 "GROUP BY query ORDER BY n DESC LIMIT 20").fetchall()
        report = self.root / "reports"
        report.mkdir(exist_ok=True)
        (report / "knowledge-gaps.md").write_text(
            "# Questions with no answer\n\n" + "".join(f"- {r['query']} ({r['n']}x)\n" for r in rows))

    # ------------------------------------------------------------ query
    def groups_for(self, user) -> list[str]:
        classes = CLASSIFICATION[:CLASSIFICATION.index(user.max_class) + 1]
        return [f"{r}/{c}" + ("" if "*" in user.depts else f"/{d}")
                for r in user.regions for c in classes for d in (["*"] if "*" in user.depts else user.depts)]

    def retrieve(self, user, question, k=5) -> list[dict]:
        """Search every region the user may read, then merge. Rank fusion inside each region
        makes every region's top hit look alike, so the merge ranks first by agreement
        (found by both keyword and vector search), then by fused score."""
        groups, hits = self.groups_for(user), []
        for r in user.regions:
            hits += hybrid_search(self.kb[r], self.emb, question, [g for g in groups if g.startswith(r + "/")], k)
        hits.sort(key=lambda h: (-len(h["found_by"]), -h["score"]))
        hits = hits[:k]
        self.q.db.execute("INSERT INTO query_log VALUES (?,?,?,?)", (now(), user.name, question, len(hits)))
        self.q.db.commit()
        return hits

    def ask(self, user, question, k=5) -> dict:
        hits = self.retrieve(user, question, k)
        if not hits:
            return {"answer": "I could not find this in the knowledge base.", "sources": []}
        from openai import OpenAI
        client = OpenAI(base_url=os.getenv("KB_BASE_URL", "http://localhost:11434/v1"), api_key="ollama")
        resp = client.chat.completions.create(
            model=os.getenv("KB_CHAT_MODEL", "qwen3:8b"), temperature=0,
            messages=[{"role": "system", "content": SYSTEM + " Reply in the language of the question."},
                      {"role": "user", "content": build_prompt(question, hits)}])
        return {"answer": resp.choices[0].message.content,
                "sources": [f"[{i}] {h['doc']} · {h['title']}" for i, h in enumerate(hits, 1)]}


def _approver():
    return User("source-policy", regions=list(REGIONS), max_class="restricted", can_approve=True)


def _read_blob_text(d) -> str:
    """Blobs are stored without extensions; copy to a temp name with the original suffix to extract."""
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / d["filename"]
        shutil.copy2(d["path"], p)
        return extract_text(p)
