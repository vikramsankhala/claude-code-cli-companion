#!/usr/bin/env bash
# Review a pull request and fail when the risk is high.   Usage: scripts/review.sh <PR-number>
# Needs: gh (signed in), claude, python3; ANTHROPIC_API_KEY for --bare runs.
set -euo pipefail
PR="${1:?usage: review.sh <PR-number>}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SCHEMA="$(cat "$HERE/schema/review.schema.json")"
gh pr diff "$PR" | claude --bare -p \
  "Review this pull request diff for bugs, security problems and missing tests. Report only real issues." \
  --output-format json --json-schema "$SCHEMA" \
  --max-turns 8 --max-budget-usd 1 > review.json
python3 "$HERE/scripts/gate.py" review.json
