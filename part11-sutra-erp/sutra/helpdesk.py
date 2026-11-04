"""Support desk: each ticket gets knowledge-base articles, live context, ranked root causes with
confidence, and suggested fixes. A person accepts, edits or rejects; the decision trains the weights."""
import re

from kb import store as kbstore
from kb.embed import get_embedder
from kb.ingest import ingest
from kb.search import hybrid_search

from .guard import redact

# symptom keywords -> candidate causes with a prior. Learned from resolved tickets in production.
CAUSES = {
    "offline": [("gateway uplink lost", 0.45), ("device certificate expired", 0.35), ("gateway disk full", 0.20)],
    "tax code": [("item group without tax mapping", 0.70), ("country pack not activated", 0.30)],
    "vibration": [("bearing wear", 0.55), ("imbalance after tool change", 0.25), ("loose mounting", 0.20)],
    "approval": [("approval matrix gap", 0.60), ("requester is the only approver", 0.40)],
}


class Helpdesk:
    def __init__(self, store, tenant, kb_path=":memory:", docs="kbdocs"):
        self.s, self.t = store, tenant
        self.emb = get_embedder()
        self.kb = kbstore.connect(kb_path)
        ingest(docs, self.kb, self.emb)
        self.n = 0

    def open(self, reporter, text, context=None) -> dict:
        self.n += 1
        clean, pii = redact(text)
        hits = hybrid_search(self.kb, self.emb, clean, ["general"], k=3)
        ctx = context or {}
        rca = self.rank_causes(clean, hits, ctx)
        ticket = {"id": f"T-{self.n:05d}", "reporter": reporter, "text": clean, "pii_removed": pii,
                  "articles": [{"title": h["title"], "score": h["score"]} for h in hits],
                  "rca": rca, "fixes": self.fixes(hits), "status": "awaiting_agent_review"}
        self.s.append(self.t, f"ticket:{ticket['id']}", "TicketOpened", ticket, reporter, "human")
        return ticket

    def rank_causes(self, text, hits, ctx):
        low = text.lower()
        scores = {}
        for kw, causes in CAUSES.items():
            if kw in low or any(kw in h["title"].lower() for h in hits[:1]):
                for cause, prior in causes:
                    scores[cause] = scores.get(cause, 0) + prior
        for cause in list(scores):                      # live evidence moves the ranking
            if cause == "bearing wear" and ctx.get("bearing_temp_rising"):
                scores[cause] += 0.3
            if cause == "item group without tax mapping" and ctx.get("config_findings", []):
                scores[cause] += 0.3
        total = sum(scores.values()) or 1
        ranked = sorted(((c, round(v / total, 2)) for c, v in scores.items()), key=lambda r: -r[1])
        return [{"cause": c, "confidence": p} for c, p in ranked]

    @staticmethod
    def fixes(hits):
        out = []
        for h in hits[:3]:
            m = re.search(r"> Resolution\n\n(.+)", h["text"], re.S)
            if m:
                out.append({"from": h["title"], "steps": m.group(1).strip()})
        return out

    def resolve(self, ticket_id, agent, accepted_cause, note):
        self.s.append(self.t, f"ticket:{ticket_id}", "TicketResolved",
                      {"accepted_cause": accepted_cause, "note": note}, agent, "human")
