"""The deterministic agent: a fixed state machine. The model is one step, fenced by a schema."""
import hashlib
import json

from .contracts import validate
from .journal import Journal
from .model import PROMPT, Model
from .policy import POLICY, decide

# The only transitions that exist. Anything else is a bug and raises.
TRANSITIONS = {
    "RECEIVED": {"EXTRACTED", "NEEDS_HUMAN"},
    "EXTRACTED": {"APPROVED", "NEEDS_HUMAN", "REJECTED"},
    "APPROVED": {"POSTED"},
}


class InvoiceAgent:
    def __init__(self, model: Model, journal: Journal, known_pos: set[str]):
        self.model, self.j, self.pos = model, journal, known_pos
        self.seen: set[tuple[str, str]] = set()
        self.results: dict[str, dict] = {}       # idempotency: run_id -> result

    def _move(self, run_id, state, new, payload):
        if new not in TRANSITIONS.get(state, set()):
            raise RuntimeError(f"illegal transition {state} -> {new}")
        self.j.append(run_id, new, payload)
        return new

    def run(self, text: str) -> dict:
        run_id = hashlib.sha256(text.encode()).hexdigest()[:12]   # same input, same run, same result
        if run_id in self.results:
            return self.results[run_id]
        self.j.append(run_id, "RECEIVED", {"chars": len(text), "policy": POLICY["version"], "model": self.model.name})
        state = "RECEIVED"
        raw = self.model.complete(PROMPT.format(text=text))
        try:
            inv = json.loads(raw)
            problems = validate(inv)
        except json.JSONDecodeError as e:
            inv, problems = None, [f"not JSON: {e.msg}"]
        if problems:
            state = self._move(run_id, state, "NEEDS_HUMAN", {"reason": "model output failed the contract", "problems": problems})
            result = {"run_id": run_id, "state": state, "reason": "model output failed the contract", "problems": problems}
        else:
            state = self._move(run_id, state, "EXTRACTED", inv)
            new, reason = decide(inv, self.pos, self.seen)
            state = self._move(run_id, state, new, {"reason": reason})
            if state == "APPROVED":
                state = self._move(run_id, state, "POSTED", {"ledger": "AP", "amount": inv["amount"], "currency": inv["currency"]})
            self.seen.add((inv["vendor"], inv["invoice_no"]))
            result = {"run_id": run_id, "state": state, "reason": reason, "invoice": inv}
        self.results[run_id] = result
        return result
