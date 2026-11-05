"""Check a P4 kit (skills, subagent, plugin manifest).  python check.py [path/to/kit]  (default: solution/my-kit)"""
import json
import re
import sys
from pathlib import Path

import yaml


def frontmatter(path: Path) -> dict:
    m = re.match(r"(?s)^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"))
    if not m:
        raise ValueError(f"{path}: no YAML frontmatter")
    return yaml.safe_load(m.group(1))


def check(kit: Path) -> list[str]:
    problems = []
    pr, rn, tr = kit / "skills/pr-summary/SKILL.md", kit / "skills/release-notes/SKILL.md", kit / "agents/test-runner.md"
    for f in (pr, rn, tr):
        if not f.exists():
            problems.append(f"missing {f.relative_to(kit)}")
    if problems:
        return problems
    a, b, c = frontmatter(pr), frontmatter(rn), frontmatter(tr)
    body_pr = pr.read_text(encoding="utf-8")
    if a.get("context") != "fork":
        problems.append("pr-summary: set context: fork")
    if "!`gh pr diff`" not in body_pr:
        problems.append("pr-summary: inject the diff with !`gh pr diff`")
    if b.get("disable-model-invocation") is not True:
        problems.append("release-notes: set disable-model-invocation: true (it is user-triggered)")
    body_rn = rn.read_text(encoding="utf-8")
    if "$0" not in body_rn or "$1" not in body_rn:
        problems.append("release-notes: use $0 and $1 for the two refs")
    tools = {t.strip() for t in str(c.get("tools", "")).split(",")}
    if tools != {"Bash", "Read", "Edit", "Grep", "Glob"}:
        problems.append(f"test-runner: tools should be Bash, Read, Edit, Grep, Glob (got {sorted(tools)})")
    if c.get("model") != "sonnet":
        problems.append("test-runner: set model: sonnet")
    for fm, f in ((a, pr), (b, rn), (c, tr)):
        if not fm.get("description"):
            problems.append(f"{f.relative_to(kit)}: add a description so Claude knows when to use it")
        if len(f.read_text(encoding="utf-8").splitlines()) > 500:
            problems.append(f"{f.relative_to(kit)}: keep it under 500 lines")
    manifest = kit / ".claude-plugin/plugin.json"
    if manifest.exists():
        m = json.loads(manifest.read_text(encoding="utf-8"))
        if not m.get("name"):
            problems.append("plugin.json: needs a name")
    return problems


if __name__ == "__main__":
    kit = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "solution" / "my-kit"
    found = check(kit)
    for p in found:
        print("✗", p)
    print("P4 checks passed" if not found else f"{len(found)} problem(s)")
    sys.exit(1 if found else 0)
