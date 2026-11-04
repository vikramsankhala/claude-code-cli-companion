#!/usr/bin/env bash
# After every edit, run the fast test suite. A failure is reported back to Claude (exit 2)
# so it fixes the regression before moving on.
cd "$CLAUDE_PROJECT_DIR" || exit 0
if ! out=$(KB_EMBEDDER=hash python -m pytest -q -x 2>&1); then
  echo "Tests failed after your edit:" >&2
  echo "$out" | tail -25 >&2
  exit 2
fi
exit 0
