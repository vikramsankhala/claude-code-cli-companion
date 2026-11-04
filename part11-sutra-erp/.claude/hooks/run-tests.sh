#!/usr/bin/env bash
# After every edit: run the suite; exit 2 feeds failures back to the agent so it fixes them.
cd "$(dirname "$0")/../.." || exit 0
if ! out=$(KB_EMBEDDER=hash python -m pytest -q 2>&1); then
  echo "$out" | tail -25 >&2
  exit 2
fi
