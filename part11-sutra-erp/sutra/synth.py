"""Synthetic evaluation data. Seeded, so every run of the suite sees the same cases.
In production a model drafts new cases from templates like these (see LLM_PROMPT); people review
them once, and the approved cases join the frozen set."""
import math
import random

LLM_PROMPT = """You write realistic ERP support tickets for testing. Cause: {cause}. Write one ticket,
in the voice of a {role}, that never names the cause directly. Vary wording, length and detail.
Return JSON: {{"text": "...", "expected_cause": "{cause}"}}"""

TEMPLATES = {
    "bearing wear": ["Line {l} spindle keeps throwing vibration warnings and the bearing feels hot",
                     "Vibration alarms again on machine M{m}; temperature creeping up since {d}"],
    "item group without tax mapping": ["Invoices for the new {g} items will not post, says tax code missing",
                                       "Cannot post sales invoice: no tax code for item group {g}"],
    "gateway uplink lost": ["All machines on line {l} went offline at once, no telemetry since {d}",
                            "Edge gateway for hall {l} shows offline and alerts have stopped"],
    "approval matrix gap": ["My purchase orders above {a} are stuck in approval, nobody gets the task",
                            "PO for {a} rupees waiting for approval for three days, approver never notified"],
}
ROLES = ["plant supervisor", "accounts clerk", "buyer", "maintenance engineer"]


def tickets(n=40, seed=3):
    rnd = random.Random(seed)
    causes = list(TEMPLATES)
    out = []
    for i in range(n):
        c = causes[i % len(causes)]
        t = rnd.choice(TEMPLATES[c]).format(l=rnd.randint(1, 6), m=rnd.randint(10, 99), d=rnd.choice(["Monday", "08:40", "yesterday"]),
                                            g=rnd.choice(["spares", "solar kits", "lab glass"]), a=rnd.choice(["2 lakh", "5,00,000"]))
        if rnd.random() < 0.3:
            t += f". Contact me on +91 98{rnd.randint(10000000, 99999999)} or ops{i}@example.com"
        out.append({"text": t, "expected_cause": c, "role": rnd.choice(ROLES)})
    return out


def telemetry(fault: str, hours=48, seed=5):
    """Hourly readings for one device. fault: none, drift (slow bearing wear) or spike (sudden failure)."""
    rnd = random.Random(seed)
    rows = []
    for h in range(hours):
        v = 3.0 + 0.4 * math.sin(h / 4) + rnd.gauss(0, 0.15)
        if fault == "drift":
            v += 0.11 * h
        if fault == "spike" and h == hours - 1:
            v = 12.5
        rows.append((float(h), round(v, 3)))
    return rows
