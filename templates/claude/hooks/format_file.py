"""PostToolUse on Edit|Write: format and lint-fix the file Claude just changed. Never blocks."""
import json
import shutil
import subprocess
import sys

data = json.load(sys.stdin)
path = (data.get("tool_input") or {}).get("file_path", "")
if path.endswith(".py") and shutil.which("ruff"):
    subprocess.run(["ruff", "check", "--fix", "--quiet", path], capture_output=True)   # fix first,
    subprocess.run(["ruff", "format", path], capture_output=True)                      # then format
sys.exit(0)
