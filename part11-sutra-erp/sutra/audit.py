"""Statutory audit (period-end, independent, read-only) and concurrent audit (continuous controls)."""
import math
from collections import Counter, defaultdict
from datetime import datetime


class StatutoryAudit:
    """Auditors get a read-only view of every event. Nothing here can write to the ledger."""

    def __init__(self, store, tenant):
        self.s, self.t = store, tenant

    def integrity(self) -> dict:
        broken = self.s.verify()
        return {"chain_intact": broken is None, "first_broken_seq": broken, "head": self.s.head()}

    def journals(self):
        return list(self.s.read(self.t, "JournalPosted"))

    def trial_balance_zero(self) -> bool:
        tot = sum(l.get("dr", 0) - l.get("cr", 0) for e in self.journals() for l in e["payload"]["lines"])
        return abs(tot) < 0.005

    def benford(self) -> dict:
        """First-digit test on journal amounts; mean absolute deviation per Nigrini's bands."""
        digits = [int(str(abs(int(e["payload"]["lines"][0].get("dr") or e["payload"]["lines"][0].get("cr"))))[0])
                  for e in self.journals() if (e["payload"]["lines"][0].get("dr") or e["payload"]["lines"][0].get("cr", 0)) >= 10]
        n = len(digits)
        if n < 50:
            return {"n": n, "mad": None, "conformity": "too few entries"}
        c = Counter(digits)
        mad = sum(abs(c[d] / n - math.log10(1 + 1 / d)) for d in range(1, 10)) / 9
        band = "close" if mad < 0.006 else "acceptable" if mad < 0.012 else "marginal" if mad < 0.015 else "nonconformity"
        return {"n": n, "mad": round(mad, 4), "conformity": band}

    def journal_entry_tests(self, round_to=10_000, manual_above=500_000) -> list[dict]:
        out = []
        for e in self.journals():
            amt = max(l.get("dr", 0) for l in e["payload"]["lines"])
            at = datetime.fromisoformat(e["at"])
            flags = []
            if at.weekday() >= 5:
                flags.append("weekend posting")
            if at.hour < 6 or at.hour >= 22:
                flags.append("out-of-hours posting")
            if amt >= round_to and amt % round_to == 0:
                flags.append("round amount")
            if e["payload"]["source"] == "manual" and amt > manual_above:
                flags.append("large manual journal")
            if flags:
                out.append({"seq": e["seq"], "amount": amt, "actor": e["actor"], "flags": flags})
        return out

    def mus_sample(self, n=5, seed=11) -> list[int]:
        """Monetary-unit sampling: larger journals are proportionally more likely to be picked."""
        js = self.journals()
        total = sum(max(l.get("dr", 0) for l in e["payload"]["lines"]) for e in js)
        if not js or total == 0:
            return []
        step, start = total / n, (seed % 97) / 97 * (total / n)
        picks, cum, k = [], 0.0, 0
        for e in js:
            cum += max(l.get("dr", 0) for l in e["payload"]["lines"])
            while k < n and start + k * step <= cum:
                picks.append(e["seq"])
                k += 1
        return sorted(set(picks))


class ConcurrentAudit:
    """Runs controls as events arrive, so problems surface in hours, not at year end."""

    def __init__(self, store, tenant, pack):
        self.s, self.t, self.pack = store, tenant, pack

    def run(self) -> list[dict]:
        findings, paid, makers = [], defaultdict(list), {}
        for e in self.s.read(self.t):
            p = e["payload"]
            if e["type"] == "PaymentProposed":
                makers[p["ref"]] = e["actor"]
            if e["type"] == "PaymentApproved" and makers.get(p["ref"]) == e["actor"]:
                findings.append({"control": "segregation of duties", "ref": p["ref"], "actor": e["actor"]})
            if e["type"] == "VendorBankChanged":
                makers[f"bank:{p['vendor']}"] = e["seq"]
            if e["type"] == "JournalPosted" and p["source"] == "payments":
                vendor = p["memo"].replace("payment to ", "")
                amt = p["lines"][0]["dr"]
                if any(abs(a - amt) < 0.01 for a in paid[vendor]):
                    findings.append({"control": "possible duplicate payment", "vendor": vendor, "amount": amt, "seq": e["seq"]})
                if f"bank:{vendor}" in makers and e["seq"] - makers[f"bank:{vendor}"] < 50:
                    findings.append({"control": "payment soon after bank-detail change", "vendor": vendor, "seq": e["seq"]})
                if amt > self.pack["approvals"]["payment_dual_control_above"] and e["actor_kind"] != "human":
                    findings.append({"control": "dual control required", "vendor": vendor, "amount": amt, "seq": e["seq"]})
                paid[vendor].append(amt)
        return findings
