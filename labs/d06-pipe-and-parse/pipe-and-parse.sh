#!/usr/bin/env bash
# D6: summarise the last 30 commits and log the run's cost.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
git log --oneline -30 \
  | claude -p "group these commits by theme" --output-format json --max-turns 3 \
  | python "$here/parse_result.py" --log "$here/runs.csv"
