"""Check a P2 settings file, then show how sample tool calls would be decided.
python check.py [path/to/.claude/settings.json]   (default: solution)

The matcher below is a simplified model of Claude Code's rule syntax, for learning:
deny beats ask, ask beats allow; 'Bash(prefix *)' matches commands starting with the prefix;
'Read(./path/**)' matches files under a folder. Claude Code itself is the authority."""
import fnmatch
import json
import sys
from pathlib import Path

DEFAULT = Path(__file__).parent / "solution" / ".claude" / "settings.json"


def _match(rule: str, tool: str, arg: str) -> bool:
    if not rule.startswith(tool + "("):
        return rule == tool
    pat = rule[len(tool) + 1:-1]
    if tool == "Bash":
        if pat.endswith(" *"):
            return arg == pat[:-2] or arg.startswith(pat[:-1])
        return arg == pat
    pat = pat.removeprefix("./")
    arg = arg.removeprefix("./")
    return fnmatch.fnmatch(arg, pat.replace("**", "*"))


def decide(perms: dict, tool: str, arg: str) -> str:
    for level in ("deny", "ask", "allow"):
        if any(_match(r, tool, arg) for r in perms.get(level, [])):
            return level
    # No rule matched: Claude Code lets read-only tools read inside the project, and asks for the rest.
    return "allow (default for reads)" if tool in ("Read", "Grep", "Glob") else "ask (no rule)"


def check(settings: dict) -> list[str]:
    p = settings.get("permissions", {})
    problems = []
    if "$schema" not in settings:
        problems.append("add the $schema line for validation in VS Code")
    if decide(p, "Bash", "python -m pytest -q") != "allow":
        problems.append("allow your test command")
    if decide(p, "Bash", "git push origin main") != "ask":
        problems.append("put git push in 'ask'")
    for f in (".env", ".env.local", "secrets/signing.key"):
        if decide(p, "Read", f) != "deny":
            problems.append(f"deny reads of {f}")
    return problems


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    s = json.loads(path.read_text(encoding="utf-8"))
    for tool, arg in [("Bash", "python -m pytest -q"), ("Bash", "git push origin main"), ("Read", ".env"),
                      ("Read", "secrets/signing.key"), ("Bash", "rm -rf build"), ("Read", "shop/cart.py")]:
        print(f"{tool}({arg})".ljust(32), "->", decide(s.get("permissions", {}), tool, arg))
    found = check(s)
    for x in found:
        print("✗", x)
    print("P2 checks passed" if not found else f"{len(found)} problem(s)")
    sys.exit(1 if found else 0)
