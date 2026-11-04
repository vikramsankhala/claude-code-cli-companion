"""Sutra: wires the modules into one tenant. Every action an agent takes passes the guard first."""
from .compliance import load_packs
from .events import EventStore
from .guard import Guard
from .helpdesk import Helpdesk
from .iot import EdgeMonitor
from .ledger import Ledger
from .remediate import propose

ACTION_AGENT = {"set_line_speed": "maintenance-agent", "create_work_order": "maintenance-agent",
                "stop_asset": "maintenance-agent", "block_payment": "ap-agent",
                "create_purchase_requisition": "maintenance-agent"}


class Sutra:
    def __init__(self, tenant="acme-in", country="IN", db=":memory:", kb_path=":memory:", packs="packs", docs="kbdocs"):
        self.store = EventStore(db)
        self.pack = load_packs(packs)[country]
        self.tenant = tenant
        self.ledger = Ledger(self.store, tenant, self.pack)
        self.edge = EdgeMonitor()
        self.guard = Guard(self.store, tenant)
        self.desk = Helpdesk(self.store, tenant, kb_path, docs)
        self.queue = []            # proposals waiting for a person

    def telemetry(self, device, metric, t, value, evidence=None):
        results = []
        for alert in self.edge.ingest(device, metric, t, value):
            self.store.append(self.tenant, f"asset:{device}", "AlertRaised", alert, "edge", "device")
            p = propose(alert, evidence or {})
            agent = ACTION_AGENT.get(p["action"], "maintenance-agent")
            if p["route"] == "auto":
                ok, why = self.guard.check(agent, p["action"])
                p["outcome"] = "executed" if ok else f"blocked: {why}"
                if not ok:
                    self.queue.append(p)
            else:
                p["outcome"] = "queued for approval" if p["route"] == "approve" else "escalated"
                self.queue.append(p)
            self.store.append(self.tenant, f"asset:{device}", "RemediationProposed",
                              {k: v for k, v in p.items() if k != "alert"} | {"alert_kind": alert["kind"]}, agent, "agent")
            results.append(p)
        return results

    def approve(self, idx, person):
        p = self.queue.pop(idx)
        agent = ACTION_AGENT.get(p["action"], "maintenance-agent")
        ok, why = self.guard.check(agent, p["action"], approved_by=person)
        self.store.append(self.tenant, "hitl", "HumanDecision", {"playbook": p["playbook"], "decision": "approved",
                                                                 "executed": ok, "why": why}, person, "human")
        return ok
