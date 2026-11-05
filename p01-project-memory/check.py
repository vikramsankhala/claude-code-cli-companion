"""Check a P1 solution: python check.py [path-to-your-practice-repo]   (default: ./solution)"""
import re
import sys
from pathlib import Path

MAX_LINES = 60


def check(root: Path) -> list[str]:
    problems = []
    claude = root / "CLAUDE.md"
    if not claude.exists():
        return ["CLAUDE.md is missing"]
    text = claude.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        problems.append(f"CLAUDE.md has {len(lines)} lines; cut it to {MAX_LINES} or fewer")
    for section in ("Commands", "Conventions", "Never"):
        if not re.search(rf"(?mi)^#+\s*{section}\b", text):
            problems.append(f"CLAUDE.md needs a '{section}' section")
    if "pytest" not in text:
        problems.append("CLAUDE.md should say how to run the tests")
    rules = list((root / ".claude" / "rules").glob("*.md"))
    scoped = [r for r in rules if re.match(r"(?s)^---\n.*?\bpaths:\s*\n\s*-\s*\S+.*?\n---", r.read_text(encoding="utf-8"))]
    if not scoped:
        problems.append("add at least one rule in .claude/rules/ with 'paths:' frontmatter")
    gi = root / ".gitignore"
    if gi.exists() and "CLAUDE.local.md" not in gi.read_text(encoding="utf-8"):
        problems.append("add CLAUDE.local.md to .gitignore")
    return problems


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "solution")
    found = check(root)
    for p in found:
        print("✗", p)
    print("P1 checks passed" if not found else f"{len(found)} problem(s)")
    sys.exit(1 if found else 0)
