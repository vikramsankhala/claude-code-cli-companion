#!/usr/bin/env bash
# Run every project's tests in its own virtual environment. Usage: ./scripts/test-all.sh
set -euo pipefail
cd "$(dirname "$0")/.."
export KB_EMBEDDER=hash
declare -A CMD=(
  [p07-mini-coder]="python test_agent.py"
  [p08-kb-rag]="python -m pytest -q"
  [p09-dms]="python -m pytest -q"
  [p10-knowledge-platform]="python -m pytest -q"
  [ch26-detagent]="python -m pytest -q"
  [part11-sutra-erp]="python -m pytest -q && python -m sutra.evals > /dev/null"
)
failed=()
for p in p07-mini-coder p08-kb-rag p09-dms p10-knowledge-platform ch26-detagent part11-sutra-erp; do
  echo "== $p"
  ( cd "$p"
    [ -d .venv ] || python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install -q -r requirements.txt
    eval "${CMD[$p]}" ) || failed+=("$p")
done
if [ ${#failed[@]} -gt 0 ]; then echo "FAILED: ${failed[*]}"; exit 1; fi
echo "All projects passed."
