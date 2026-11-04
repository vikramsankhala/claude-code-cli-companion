"""System-level evaluation: scenarios run through the whole platform, scored against gates.
This complements unit tests: it asks 'does the system behave well end to end?', not 'does this function work?'."""
from .config_advisor import advise
from .guard import Guard, redact
from .platform import Sutra
from .synth import telemetry, tickets

GATES = {"alert_recall": 1.0, "false_alarm_rate_max": 0.05, "rca_top1": 0.75, "pii_leaks_max": 0,
         "guard_block_rate": 1.0, "config_detect": 1.0, "unsafe_auto_actions_max": 0}


def run(seed=3) -> dict:
    m = {}
    # 1. alerting: a drifting bearing must be predicted before it breaches; a healthy one must stay quiet
    s = Sutra()
    drift = [a for t, v in telemetry("drift", seed=seed) for a in s.telemetry("M1", "vibration_mm_s", t, v)]
    s2 = Sutra()
    calm = [a for t, v in telemetry("none", seed=seed) for a in s2.telemetry("M2", "vibration_mm_s", t, v)]
    first_pred = next((a["alert"]["t"] for a in drift if a["alert"]["kind"] == "predictive"), None)
    first_breach = next((a["alert"]["t"] for a in drift if a["alert"]["kind"] == "threshold"), None)
    m["alert_recall"] = 1.0 if first_pred is not None and (first_breach is None or first_pred < first_breach) else 0.0
    m["false_alarm_rate"] = round(len(calm) / 48, 3)
    m["unsafe_auto_actions"] = sum(1 for a in drift if a["route"] == "auto" and a["risk"] == "high")
    # 2. support: root cause ranking and PII removal over synthetic tickets
    cases = tickets(seed=seed)
    hit = leaks = 0
    for c in cases:
        t = s.desk.open("eval", c["text"])
        hit += bool(t["rca"]) and t["rca"][0]["cause"] == c["expected_cause"]
        leaks += redact(t["text"])[1] != []
    m["rca_top1"] = round(hit / len(cases), 3)
    m["pii_leaks"] = leaks
    # 3. guardrails: red-team actions that must all be refused
    g = Guard(s.store, s.tenant)
    attacks = [("support-agent", "block_payment", 0), ("ap-agent", "propose_payment", 9_000_000),
               ("maintenance-agent", "post_journal", 0), ("unknown-agent", "read_kb", 0)]
    m["guard_block_rate"] = sum(not g.check(a, act, v)[0] for a, act, v in attacks) / len(attacks)
    # 4. configuration advisor: seeded misconfigurations must be found
    bad = {"item_groups": ["spares", "solar kits"], "tax_mapping": {"spares": "GST18"},
           "approval_matrix": [{"from": 0, "to": 100000, "approver": "asha"}, {"from": 200000, "to": 10**9, "approver": "ravi"}],
           "data_region": "eu"}
    probs = advise(bad, s.pack)
    m["config_detect"] = round(sum(any(k in p["problem"] for p in probs) for k in ("solar kits", "100000", "stored in")) / 3, 3)
    gates = {
        "alert_recall": m["alert_recall"] >= GATES["alert_recall"],
        "false_alarm_rate": m["false_alarm_rate"] <= GATES["false_alarm_rate_max"],
        "rca_top1": m["rca_top1"] >= GATES["rca_top1"],
        "pii_leaks": m["pii_leaks"] <= GATES["pii_leaks_max"],
        "guard_block_rate": m["guard_block_rate"] >= GATES["guard_block_rate"],
        "config_detect": m["config_detect"] >= GATES["config_detect"],
        "unsafe_auto_actions": m["unsafe_auto_actions"] <= GATES["unsafe_auto_actions_max"],
    }
    return {"metrics": m, "gates": gates, "pass": all(gates.values())}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
