"""Stop: run the fast test suite. If it fails, tell Claude to keep working, with the failure summary."""
import json
import os
import subprocess
import sys

data = json.load(sys.stdin)
if data.get("stop_hook_active"):          # already continuing because of this hook: do not loop forever
    sys.exit(0)
root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
try:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "--no-header"], cwd=root,
                       capture_output=True, text=True, timeout=120)
except subprocess.TimeoutExpired:
    print(json.dumps({"decision": "block", "reason": "The test suite timed out after 120 s. Find the slow or hanging test."}))
    sys.exit(0)
if r.returncode not in (0, 5):            # 5 = no tests collected
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-15:])
    print(json.dumps({"decision": "block", "reason": f"Tests are failing. Fix them before finishing:\n{tail}"}))
sys.exit(0)
