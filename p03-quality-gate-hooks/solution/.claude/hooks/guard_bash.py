"""PreToolUse on Bash: refuse destructive commands. Exit 2 blocks the call and shows Claude the reason."""
import json
import re
import sys

cmd = (json.load(sys.stdin).get("tool_input") or {}).get("command", "")
RULES = [
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b[^;&|]*\s(/|/\*|~|~/|\$HOME|\$HOME/)(\s|$)",
     "recursive delete of the root or home folder"),
    (r"\bgit\s+push\b[^;&|]*\s(--force|-f|--force-with-lease)\b", "force push"),
    (r"\bgit\s+push\b[^;&|]*\s\+\S+", "force push (+refspec)"),
]
for pattern, why in RULES:
    if re.search(pattern, cmd):
        print(f"Blocked by project hook: {why}. Ask the user to run it themselves if it is really intended.",
              file=sys.stderr)
        sys.exit(2)
sys.exit(0)
