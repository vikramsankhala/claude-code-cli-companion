import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from sutra.audit import ConcurrentAudit, StatutoryAudit
from sutra.compliance import load_packs, tax
from sutra.config_advisor import advise
from sutra.evals import run
from sutra.events import EventStore
from sutra.guard import AgentMonitor, Guard, redact
from sutra.iot import EdgeMonitor
from sutra.ledger import Ledger
from sutra.optimize import brute_force, decode, maintenance_qubo, production_plan, solve_qubo
from sutra.platform import Sutra
from sutra.remediate import confidence, route
from sutra.synth import telemetry

PACKS = load_packs()


def test_packs_and_tax():
    assert set(PACKS) == {"IN", "DE", "US"}
    assert tax(PACKS["IN"], 1000) == 180.0 and tax(PACKS["DE"], 1000) == 190.0


def test_ledger_balances_and_rejects_unbalanced():
    s = EventStore()
    led = Ledger(s, "t", PACKS["IN"])
    led.sale("Kaveri Retail", 10_000)
    led.purchase("Nilgiri Paper", 4_000)
    assert abs(sum(led.trial_balance().values())) < 0.01
    with pytest.raises(ValueError):
        led.post([{"acct": "1000", "dr": 5}, {"acct": "4000", "cr": 4}], "bad", "x")


def test_events_append_only_and_tamper_evident(tmp_path):
    db = tmp_path / "e.sqlite"
    s = EventStore(str(db))
    Ledger(s, "t", PACKS["IN"]).sale("A", 100)
    with pytest.raises(sqlite3.DatabaseError):
        s.db.execute("UPDATE events SET payload='{}'")
    s.db.rollback()
    s.db.close()
    raw = sqlite3.connect(db)                       # an attacker with file access drops the trigger
    raw.execute("DROP TRIGGER ev_no_update")
    raw.execute("UPDATE events SET payload = replace(payload, '100', '10')")
    raw.commit()
    assert EventStore(str(db)).verify() == 1


def test_predictive_alert_before_threshold():
    m, kinds = EdgeMonitor(), []
    for t, v in telemetry("drift"):
        kinds += [(a["kind"], t) for a in m.ingest("M1", "vibration_mm_s", t, v)]
    pred = min(t for k, t in kinds if k == "predictive")
    breach = min(t for k, t in kinds if k == "threshold")
    assert pred < breach


def test_spike_raises_critical_and_anomaly():
    m, alerts = EdgeMonitor(), []
    for t, v in telemetry("spike"):
        alerts += m.ingest("M1", "vibration_mm_s", t, v)
    kinds = {(a["kind"], a["severity"]) for a in alerts}
    assert ("threshold", "critical") in kinds and ("anomaly", "warning") in kinds


def test_milp_plan_respects_capacity():
    plan, margin = production_plan({"pump": (1200, {"cnc": 2, "paint": 1}, 40), "valve": (700, {"cnc": 1, "paint": 1}, 60)},
                                   {"cnc": 80, "paint": 70})
    assert 2 * plan["pump"] + plan["valve"] <= 80 and plan["pump"] + plan["valve"] <= 70
    assert margin == 1200 * plan["pump"] + 700 * plan["valve"]


def test_qubo_annealer_matches_brute_force():
    jobs = {"press": 3.0, "lathe": 1.0, "oven": 2.0}
    Q, idx = maintenance_qubo(jobs, 2, clash=[("press", "oven")])
    x, e, solver = solve_qubo(Q, len(idx))
    bx, be = brute_force(Q, len(idx))
    assert solver == "local-anneal" and e == pytest.approx(be)
    sched = decode(x, idx)
    assert set(sched) == set(jobs) and sched["press"] != sched["oven"]


def test_hitl_routing_by_confidence_and_risk():
    crit = {"kind": "threshold", "severity": "critical"}
    assert confidence(crit, {"corroborating": 2, "past_success_rate": 1.0}) == 1.0
    assert route("reduce_load", 0.95) == "auto"
    assert route("reduce_load", 0.7) == "approve"
    assert route("stop_machine", 1.0) == "approve"       # high risk never runs alone
    assert route("schedule_maintenance", 0.3) == "escalate"


def test_guard_blocks_and_suspends():
    s = EventStore()
    g = Guard(s, "t")
    assert g.check("support-agent", "read_kb")[0]
    assert not g.check("ap-agent", "propose_payment", 9_000_000)[0]
    for _ in range(5):
        g.check("support-agent", "block_payment")
    assert "support-agent" in g.killed
    assert not g.check("support-agent", "read_kb")[0]
    assert any(f["finding"] == "attempted actions outside its role" for f in AgentMonitor(s, "t").findings())


def test_pii_redaction():
    text, found = redact("PAN ABCDE1234F, mail ravi@acme.in, phone +91 98195 43261")
    assert "ABCDE1234F" not in text and "ravi@acme.in" not in text and {"pan", "email", "phone"} <= set(found)


def test_statutory_and_concurrent_audit():
    s = EventStore()
    led = Ledger(s, "t", PACKS["IN"])
    sat = datetime(2026, 11, 7, 23, 30, tzinfo=timezone.utc).isoformat()
    led.post([{"acct": "6100", "dr": 600_000}, {"acct": "1000", "cr": 600_000}], "year-end adj", "kiran", at=sat)
    s.append("t", "pay:1", "PaymentProposed", {"ref": "P1"}, "meena", "human")
    s.append("t", "pay:1", "PaymentApproved", {"ref": "P1"}, "meena", "human")
    s.append("t", "vendor:V", "VendorBankChanged", {"vendor": "Lake Steel"}, "meena", "human")
    led.pay("Lake Steel", 1_500_000, "ap-agent", "agent")
    led.pay("Lake Steel", 1_500_000, "ap-agent", "agent")
    st = StatutoryAudit(s, "t")
    assert st.integrity()["chain_intact"] and st.trial_balance_zero()
    flags = st.journal_entry_tests()[0]["flags"]
    assert {"weekend posting", "out-of-hours posting", "round amount", "large manual journal"} <= set(flags)
    controls = {f["control"] for f in ConcurrentAudit(s, "t", PACKS["IN"]).run()}
    assert {"segregation of duties", "possible duplicate payment", "payment soon after bank-detail change",
            "dual control required"} <= controls
    assert AgentMonitor(s, "t").findings()


def test_helpdesk_rca_and_fix():
    s = Sutra()
    t = s.desk.open("asha", "Vibration warnings on M12 again, bearing hot. Call me on +91 98195 43261",
                    {"bearing_temp_rising": True})
    assert t["rca"][0]["cause"] == "bearing wear" and t["rca"][0]["confidence"] > 0.5
    assert "phone" in t["pii_removed"] and t["fixes"]
    assert t["articles"][0]["title"].startswith("High vibration")


def test_config_advisor():
    probs = advise({"item_groups": ["spares"], "tax_mapping": {}, "approval_matrix":
                    [{"from": 0, "to": 50_000, "approver": "a", "requesters": ["a"]}], "data_region": "in"}, PACKS["IN"])
    text = " ".join(p["problem"] for p in probs)
    assert "spares" in text and "own requests" in text and "stored in" not in text


def test_platform_end_to_end_with_hitl():
    s = Sutra()
    out = []
    for t, v in telemetry("spike"):
        out += s.telemetry("M7", "bearing_temp_c", t, v * 8)     # scaled into the temperature range
    assert any(p["playbook"] == "stop_machine" and p["route"] != "auto" for p in out)
    i = next(i for i, p in enumerate(s.queue) if p["playbook"] == "stop_machine")
    assert s.approve(i, "plant-head")
    assert s.store.verify() is None


def test_system_eval_gates_pass():
    r = run()
    assert r["pass"], r
