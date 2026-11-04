"""Guardrails for agents: policy check before every action, PII redaction on every output, and a
monitor that trips a kill switch when an agent's behaviour departs from its baseline."""
import re
import time
from collections import defaultdict, deque

PII = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    "aadhaar": re.compile(r"\b[2-9][0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b"),
    "iban": re.compile(r"\b[A-Z]{2}[0-9]{2}(?:\s?[A-Z0-9]{4}){3,7}\b"),
    "phone": re.compile(r"(?<!\w)\+?[0-9][0-9 ()-]{8,}[0-9]\b"),
}


def redact(text: str) -> tuple[str, list[str]]:
    found = []
    for name, rx in PII.items():
        if rx.search(text):
            found.append(name)
            text = rx.sub(f"[{name.upper()}]", text)
    return text, found


AGENT_POLICY = {
    "maintenance-agent": {"allow": {"create_work_order", "set_line_speed", "read_telemetry", "stop_asset",
                                    "create_purchase_requisition"}, "max_per_min": 20, "max_value": 0,
                          "needs_approval": {"stop_asset"}},
    "ap-agent": {"allow": {"read_invoice", "propose_payment", "block_payment"}, "max_per_min": 30, "max_value": 250_000},
    "support-agent": {"allow": {"read_kb", "comment_ticket", "propose_fix"}, "max_per_min": 60, "max_value": 0},
}


class Guard:
    def __init__(self, store, tenant, clock=time.time):
        self.s, self.t, self.clock = store, tenant, clock
        self.calls = defaultdict(deque)
        self.denials = defaultdict(int)
        self.killed: set[str] = set()

    def check(self, agent, action, value=0.0, approved_by=None) -> tuple[bool, str]:
        now = self.clock()
        pol = AGENT_POLICY.get(agent)
        if agent in self.killed:
            ok, why = False, "agent is suspended"
        elif pol is None:
            ok, why = False, "unknown agent"
        elif action not in pol["allow"]:
            ok, why = False, f"action {action} not allowed"
        elif action in pol.get("needs_approval", set()) and approved_by is None:
            ok, why = False, f"action {action} needs a named human approver"
        elif value > pol["max_value"] and approved_by is None:
            ok, why = False, "value above agent limit; needs a human approver"
        else:
            q = self.calls[agent]
            while q and now - q[0] > 60:
                q.popleft()
            ok, why = (len(q) < pol["max_per_min"]), "rate limit"
            if ok:
                q.append(now)
                why = "allowed"
        self.denials[agent] = 0 if ok else self.denials[agent] + 1
        self.s.append(self.t, f"agent:{agent}", "GuardDecision",
                      {"action": action, "value": value, "allowed": ok, "why": why, "approved_by": approved_by},
                      "guard", "system")
        if self.denials[agent] >= 5 and agent not in self.killed:   # repeated attempts at forbidden actions
            self.kill(agent, "five consecutive denials")
        return ok, why

    def kill(self, agent, reason):
        self.killed.add(agent)
        self.s.append(self.t, f"agent:{agent}", "AgentSuspended", {"reason": reason}, "guard", "system")


class AgentMonitor:
    """Watches the event stream for aberrations the policy check alone cannot see."""

    def __init__(self, store, tenant):
        self.s, self.t = store, tenant

    def findings(self) -> list[dict]:
        out, per_agent = [], defaultdict(list)
        for e in self.s.read(self.t, "GuardDecision"):
            per_agent[e["stream"].split(":", 1)[1]].append(e)
        for agent, evs in per_agent.items():
            denied = sum(not e["payload"]["allowed"] for e in evs)
            if evs and denied / len(evs) > 0.2:
                out.append({"agent": agent, "finding": "high denial ratio", "ratio": round(denied / len(evs), 2)})
            actions = {e["payload"]["action"] for e in evs}
            novel = actions - AGENT_POLICY.get(agent, {}).get("allow", set())
            if novel:
                out.append({"agent": agent, "finding": "attempted actions outside its role", "actions": sorted(novel)})
        for e in self.s.read(self.t, "JournalPosted"):
            if e["actor_kind"] == "agent" and e["payload"]["source"] == "payments":
                out.append({"agent": e["actor"], "finding": "agent posted a payment directly", "seq": e["seq"]})
        return out
