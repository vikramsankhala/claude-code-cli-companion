"""Check a PLAN.md before you start agents: goal, 2 to 3 tasks, no shared files, risks, done criteria.
python scripts/check_plan.py PLAN.md"""
import re
import sys
from pathlib import Path


def parse(text: str) -> dict:
    tasks = {}
    for m in re.finditer(r"(?ms)^### Task: (\S+)\s*\n(.*?)(?=^### |^## |\Z)", text):
        files = re.search(r"(?m)^- Files: (.+)$", m.group(2))
        done = re.search(r"(?m)^- Done when: (.+)$", m.group(2))
        tasks[m.group(1)] = {"files": [f.strip() for f in files.group(1).split(",")] if files else [],
                             "done": done.group(1).strip() if done else ""}
    return {"goal": bool(re.search(r"(?m)^## Goal\n+\S", text)), "risks": bool(re.search(r"(?m)^## Risks\n+- ", text)),
            "done": bool(re.search(r"(?m)^## Done when", text)), "tasks": tasks}


def check(text: str) -> list[str]:
    p, problems = parse(text), []
    if not p["goal"]:
        problems.append("write the Goal")
    if not 2 <= len(p["tasks"]) <= 3:
        problems.append(f"split the work into 2 or 3 tasks (found {len(p['tasks'])})")
    seen = {}
    for name, t in p["tasks"].items():
        if not t["files"]:
            problems.append(f"task {name}: list its files")
        if not t["done"]:
            problems.append(f"task {name}: say how you will know it is done")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,40}", name):
            problems.append(f"task {name}: use a short lowercase name; it becomes the worktree name")
        for f in t["files"]:
            if f in seen:
                problems.append(f"tasks {seen[f]} and {name} both touch {f}; agents in parallel must not share files")
            seen[f] = name
    if not p["risks"]:
        problems.append("list at least one risk")
    if not p["done"]:
        problems.append("add the 'Done when' checklist")
    return problems


if __name__ == "__main__":
    found = check(Path(sys.argv[1] if len(sys.argv) > 1 else "PLAN.md").read_text(encoding="utf-8"))
    for x in found:
        print("✗", x)
    print("Plan is ready for parallel agents" if not found else f"{len(found)} problem(s)")
    sys.exit(1 if found else 0)
