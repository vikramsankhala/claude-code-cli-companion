"""Double-entry ledger on top of the event store. A journal that does not balance is never written."""
from collections import defaultdict

from .compliance import tax

ACCOUNTS = {"1000": "Bank", "1200": "Receivables", "1300": "Inventory", "2000": "Payables",
            "2100": "Tax payable", "2150": "Input tax", "4000": "Revenue", "5000": "Cost of goods", "6100": "Maintenance"}


class Ledger:
    def __init__(self, store, tenant, pack):
        self.s, self.t, self.pack = store, tenant, pack

    def post(self, lines, memo, actor, actor_kind="human", source="manual", at=None):
        dr = round(sum(l.get("dr", 0) for l in lines), 2)
        cr = round(sum(l.get("cr", 0) for l in lines), 2)
        if dr != cr or dr <= 0:
            raise ValueError(f"unbalanced journal: dr {dr} cr {cr}")
        for l in lines:
            if l["acct"] not in ACCOUNTS:
                raise ValueError(f"unknown account {l['acct']}")
        return self.s.append(self.t, "gl", "JournalPosted",
                             {"lines": lines, "memo": memo, "source": source, "currency": self.pack["currency"]},
                             actor, actor_kind, at)

    def sale(self, customer, net, actor="sales-bot", actor_kind="agent", at=None):
        t = tax(self.pack, net)
        return self.post([{"acct": "1200", "dr": net + t}, {"acct": "4000", "cr": net}, {"acct": "2100", "cr": t}],
                         f"sale to {customer}", actor, actor_kind, "sales", at)

    def purchase(self, vendor, net, actor="ap-bot", actor_kind="agent", at=None):
        t = tax(self.pack, net)
        return self.post([{"acct": "1300", "dr": net}, {"acct": "2150", "dr": t}, {"acct": "2000", "cr": net + t}],
                         f"purchase from {vendor}", actor, actor_kind, "purchasing", at)

    def pay(self, vendor, amount, actor, actor_kind="human", at=None):
        return self.post([{"acct": "2000", "dr": amount}, {"acct": "1000", "cr": amount}],
                         f"payment to {vendor}", actor, actor_kind, "payments", at)

    def trial_balance(self) -> dict:
        tb = defaultdict(float)
        for e in self.s.read(self.t, "JournalPosted"):
            for l in e["payload"]["lines"]:
                tb[l["acct"]] += l.get("dr", 0) - l.get("cr", 0)
        return {k: round(v, 2) for k, v in sorted(tb.items())}
