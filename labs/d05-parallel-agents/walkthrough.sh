#!/usr/bin/env bash
# D5 by hand: create two worktrees yourself and run one interactive agent in each terminal.
set -euo pipefail
git rev-parse --is-inside-work-tree > /dev/null || { echo "Run inside the practice app's git repository"; exit 1; }
git worktree add -b add-health ../shopkeeper-health
git worktree add -b docs-pass ../shopkeeper-docs
cat <<'MSG'
Terminal 1:  cd ../shopkeeper-health && claude "add a GET /health endpoint with a test"
Terminal 2:  cd ../shopkeeper-docs   && claude "improve README setup instructions"
When done:   git merge add-health docs-pass && git worktree remove ../shopkeeper-health ../shopkeeper-docs
MSG
