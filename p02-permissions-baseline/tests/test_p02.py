import json

from check import DEFAULT, check, decide

S = json.loads(DEFAULT.read_text())
P = S["permissions"]


def test_solution_passes():
    assert check(S) == []


def test_precedence_and_matching():
    assert decide(P, "Bash", "ruff check .") == "allow"
    assert decide(P, "Bash", "git push --force origin main") == "deny"      # deny beats ask
    assert decide(P, "Bash", "git diff-index HEAD") == "ask (no rule)"      # 'git diff *' needs the space
    assert decide(P, "Read", "shop/cart.py") == "allow (default for reads)"
    assert decide(P, "Edit", "secrets/signing.key") == "deny"


def test_detects_missing_rules():
    assert "deny reads of .env" in " ".join(check({"permissions": {"allow": []}}))
