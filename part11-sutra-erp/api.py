"""Investor-demo API. Run: KB_EMBEDDER=hash uvicorn api:app --reload, then open /docs."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sutra.audit import ConcurrentAudit, StatutoryAudit
from sutra.evals import run as run_evals
from sutra.guard import AgentMonitor
from sutra.platform import Sutra

app = FastAPI(title="Sutra ERP proof of concept")
S = Sutra(db="sutra.sqlite")


class Reading(BaseModel):
    device: str
    metric: str
    t: float
    value: float


class Ticket(BaseModel):
    reporter: str
    text: str


@app.post("/telemetry")
def telemetry(r: Reading):
    return S.telemetry(r.device, r.metric, r.t, r.value)


@app.get("/hitl/queue")
def queue():
    return [{"idx": i, **{k: p[k] for k in ("playbook", "risk", "confidence", "route")}} for i, p in enumerate(S.queue)]


@app.post("/hitl/approve/{idx}")
def approve(idx: int, person: str):
    if not 0 <= idx < len(S.queue):
        raise HTTPException(404, "no such proposal")
    return {"executed": S.approve(idx, person)}


@app.post("/tickets")
def ticket(t: Ticket):
    return S.desk.open(t.reporter, t.text)


@app.get("/audit/statutory")
def statutory():
    a = StatutoryAudit(S.store, S.tenant)
    return {"integrity": a.integrity(), "trial_balance_zero": a.trial_balance_zero(),
            "journal_flags": a.journal_entry_tests(), "sample": a.mus_sample()}


@app.get("/audit/concurrent")
def concurrent():
    return {"controls": ConcurrentAudit(S.store, S.tenant, S.pack).run(),
            "agents": AgentMonitor(S.store, S.tenant).findings()}


@app.get("/evals")
def evals():
    return run_evals()
