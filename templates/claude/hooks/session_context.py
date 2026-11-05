"""SessionStart: tell Claude the current branch and the open TODOs, so it starts with context."""
import json
import os
import subprocess
from pathlib import Path

root = Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
try:
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True).stdout.strip()
except FileNotFoundError:
    branch = ""
todos = []
for f in sorted(root.rglob("*.py")):
    if any(part in (".venv", "__pycache__") for part in f.parts):
        continue
    for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if "TODO" in line:
            todos.append(f"{f.relative_to(root)}:{i}: {line.strip()}")
text = f"Current branch: {branch or 'unknown'}.\n"
text += ("Open TODOs:\n" + "\n".join(todos[:20])) if todos else "No open TODOs."
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
