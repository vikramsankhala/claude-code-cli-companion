"""Deterministic business rules. Plain data, so auditors can read them and tests can pin them."""
POLICY = {
    "version": "2026.11-1",
    "auto_approve_limit": {"INR": 250_000, "EUR": 2_500, "USD": 3_000},
    "hard_limit": {"INR": 5_000_000, "EUR": 50_000, "USD": 60_000},
    "require_po_above": {"INR": 50_000, "EUR": 500, "USD": 600},
    "blocked_vendors": ["Shadow Supplies Ltd"],
}


def decide(inv: dict, known_pos: set[str], seen_invoices: set[tuple[str, str]]) -> tuple[str, str]:
    """Return (state, reason). Order matters and is fixed: blocks first, then limits, then approvals."""
    cur, amt = inv["currency"], inv["amount"]
    if inv["vendor"] in POLICY["blocked_vendors"]:
        return "REJECTED", "vendor is blocked"
    if (inv["vendor"], inv["invoice_no"]) in seen_invoices:
        return "REJECTED", "duplicate invoice"
    if amt > POLICY["hard_limit"][cur]:
        return "REJECTED", "above hard limit"
    if amt > POLICY["require_po_above"][cur] and inv["po_number"] is None:
        return "NEEDS_HUMAN", "purchase order required"
    if inv["po_number"] is not None and inv["po_number"] not in known_pos:
        return "NEEDS_HUMAN", "unknown purchase order"
    if amt > POLICY["auto_approve_limit"][cur]:
        return "NEEDS_HUMAN", "above auto-approval limit"
    return "APPROVED", "within policy"
