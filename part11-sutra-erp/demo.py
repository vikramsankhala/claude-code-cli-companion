"""The five-minute investor demo, as a script: python demo.py"""
import os

os.environ.setdefault("KB_EMBEDDER", "hash")

from sutra.audit import ConcurrentAudit, StatutoryAudit   # noqa: E402
from sutra.optimize import maintenance_qubo, solve_qubo, decode, production_plan   # noqa: E402
from sutra.platform import Sutra                            # noqa: E402
from sutra.synth import telemetry                           # noqa: E402

s = Sutra()
print("1  Business as usual: a sale and a purchase post with GST")
s.ledger.sale("Kaveri Retail", 120_000)
s.ledger.purchase("Nilgiri Paper", 40_000)
print("   trial balance:", s.ledger.trial_balance())

print("2  A bearing starts to wear. The edge predicts the breach before it happens")
for t, v in telemetry("drift"):
    for p in s.telemetry("M1", "vibration_mm_s", t, v, {"corroborating": 1, "past_success_rate": .9}):
        print(f"   t={t:>4.0f}h {p['alert']['kind']:<10} {p['alert']['why']:<28} -> {p['playbook']:<20} "
              f"conf {p['confidence']:.2f} {p['route']:<8} {p['outcome']}")

print("3  Plan the fix: MILP for production, QUBO for the maintenance window")
plan, margin = production_plan({"pump": (1200, {"cnc": 2, "paint": 1}, 40), "valve": (700, {"cnc": 1, "paint": 1}, 60)},
                               {"cnc": 80, "paint": 70})
print("   production plan", plan, "margin", margin)
Q, idx = maintenance_qubo({"M1": 3.0, "press": 1.0, "oven": 2.0}, 3, clash=[("M1", "oven")])
x, e, solver = solve_qubo(Q, len(idx))
print("   maintenance slots", decode(x, idx), "via", solver)

print("4  An operator raises a ticket; the desk brings articles, causes and fixes")
t = s.desk.open("asha", "Vibration alarms again on M1, bearing hot. Call +91 98195 43261", {"bearing_temp_rising": True})
print("   ", t["id"], "PII removed:", t["pii_removed"])
for c in t["rca"][:3]:
    print(f"    cause {c['cause']:<30} {c['confidence']:.2f}")

print("5  Auditors: integrity, journal tests and continuous controls")
print("   ", StatutoryAudit(s.store, s.tenant).integrity())
print("    controls:", ConcurrentAudit(s.store, s.tenant, s.pack).run() or "no findings")
