"""Start one background Claude Code agent per task in PLAN.md, each in its own worktree.
python scripts/start_tasks.py PLAN.md            (add --dry-run to print the commands only)"""
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_plan import check, parse  # noqa: E402

plan_path = Path(next((a for a in sys.argv[1:] if not a.startswith("--")), "PLAN.md"))
text = plan_path.read_text(encoding="utf-8")
problems = check(text)
if problems:
    sys.exit("Fix the plan first:\n" + "\n".join(problems))
for name, t in parse(text)["tasks"].items():
    prompt = (f"Read {plan_path.name}. Do only the task '{name}', touching only these files: {', '.join(t['files'])}. "
              f"Done when: {t['done']}. Run the tests, then commit with a clear message.")
    cmd = ["claude", "-w", name, "--bg", prompt]
    print(" ".join(shlex.quote(c) for c in cmd))
    if "--dry-run" not in sys.argv:
        subprocess.run(cmd, check=True)
print("Watch them with: claude agents")
