"""PreToolUse hook on Bash, cross-platform (no jq needed). Exit 2 blocks the call; stderr is the reason Claude reads.
Catches rm -rf, -fr, -Rf and --recursive --force aimed at /, ~ or $HOME (and anything under them)."""
import json
import re
import sys

FLAGS = r"(?:-[a-zA-Z]*[rR][a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*[rR][a-zA-Z]*|(?:--recursive\s+--force|--force\s+--recursive))"
PATTERN = re.compile(rf"\brm\s+(?:-\S+\s+)*{FLAGS}\s+(?:-\S+\s+)*[\"']?(/|~|\$HOME|\$\{{HOME\}})")


def check(command: str) -> str | None:
    if PATTERN.search(command):
        return "Blocked: recursive delete of a root or home path. Ask the user to run it themselves if intended."
    return None


if __name__ == "__main__":
    event = json.load(sys.stdin)
    reason = check((event.get("tool_input") or {}).get("command", ""))
    if reason:
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)
