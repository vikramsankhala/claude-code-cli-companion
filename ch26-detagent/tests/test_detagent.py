import json

import pytest

from detagent.agent import InvoiceAgent
from detagent.journal import Journal
from detagent.model import PROMPT, Cassette, key

INVOICES = {
    "small": "Invoice INV-1001 from Nilgiri Paper Co. Amount payable INR 18,400.00. No PO.",
    "po": "Invoice INV-2002, Rhein Tools GmbH, EUR 1,980.50 against PO-12345.",
    "big": "Invoice INV-3003 from Nilgiri Paper Co. INR 9,40,000 against PO-12345.",
    "nopo": "Invoice INV-4004, Lake Steel Inc, USD 4,200, purchase order not quoted.",
    "bad": "Invoice ??? from somebody, amount unclear.",
    "dup": "RESENT: Invoice INV-1001 from Nilgiri Paper Co., INR 18,400.00.",
}
OUTPUTS = {
    "small": {"vendor": "Nilgiri Paper Co.", "invoice_no": "INV-1001", "currency": "INR", "amount": 18400.0, "po_number": None},
    "po": {"vendor": "Rhein Tools GmbH", "invoice_no": "INV-2002", "currency": "EUR", "amount": 1980.5, "po_number": "PO-12345"},
    "big": {"vendor": "Nilgiri Paper Co.", "invoice_no": "INV-3003", "currency": "INR", "amount": 940000, "po_number": "PO-12345"},
    "nopo": {"vendor": "Lake Steel Inc", "invoice_no": "INV-4004", "currency": "USD", "amount": 4200, "po_number": None},
    "bad": "Sure! Here is the JSON: {vendor: somebody}",
}
OUTPUTS["dup"] = OUTPUTS["small"]


@pytest.fixture
def cassette(tmp_path):
    tape = {key("devstral", PROMPT.format(text=INVOICES[k])): (v if isinstance(v, str) else json.dumps(v))
            for k, v in OUTPUTS.items()}
    p = tmp_path / "c.json"
    p.write_text(json.dumps(tape))
    return Cassette(p, name="devstral")


def agent(cassette, path=":memory:"):
    return InvoiceAgent(cassette, Journal(path), {"PO-12345"})


def test_decisions(cassette):
    a = agent(cassette)
    got = {k: a.run(t)["state"] for k, t in INVOICES.items()}
    assert got == {"small": "POSTED", "po": "POSTED", "big": "NEEDS_HUMAN", "nopo": "NEEDS_HUMAN", "bad": "NEEDS_HUMAN", "dup": "REJECTED"}


def test_same_input_same_journal(cassette, tmp_path):
    heads = []
    for i in range(2):
        a = agent(cassette, str(tmp_path / f"j{i}.sqlite"))
        for t in INVOICES.values():
            a.run(t)
        heads.append(a.j.head())
    assert heads[0] == heads[1]


def test_idempotent(cassette):
    a = agent(cassette)
    r1, r2 = a.run(INVOICES["small"]), a.run(INVOICES["small"])
    assert r1 == r2 and a.j.steps(r1["run_id"]).count("POSTED") == 1


def test_contract_failure_goes_to_human(cassette):
    r = agent(cassette).run(INVOICES["bad"])
    assert r["state"] == "NEEDS_HUMAN" and r["problems"]


def test_tamper_is_detected(cassette):
    a = agent(cassette)
    for t in INVOICES.values():
        a.run(t)
    assert a.j.verify() is None
    a.j.db.execute("UPDATE journal SET payload = replace(payload, '18400.0', '1840.0') WHERE step='EXTRACTED'")
    assert a.j.verify() is not None


def test_replay_never_calls_network(tmp_path):
    with pytest.raises(LookupError):
        Cassette(tmp_path / "empty.json").complete("unrecorded prompt")


def test_duplicate_rejected(cassette):
    a = agent(cassette)
    a.run(INVOICES["small"])
    r = a.run(INVOICES["dup"])              # different wording, same vendor and invoice number
    assert r["state"] == "REJECTED" and r["reason"] == "duplicate invoice"
