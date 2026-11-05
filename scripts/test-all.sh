#!/usr/bin/env bash
# Run every project's tests in its own virtual environment. Usage: ./scripts/test-all.sh [folder ...]
set -euo pipefail
cd "$(dirname "$0")/.."
export KB_EMBEDDER=hash PYTHONUTF8=1 MPLBACKEND=Agg
declare -A CMD=(
  [p07-mini-coder]="python test_agent.py && python test_agent_extended.py"
  [part11-sutra-erp]="python -m pytest -q && python -m sutra.evals > /dev/null"
  [workbench]="python -m pytest -q tests practice/fintech"
)
declare -A REQ=( [workbench]="requirements-ci.txt" )
ALL=(sample-app p01-project-memory p02-permissions-baseline p03-quality-gate-hooks p04-skills-agents-kit
     p05-ci-reviewer p06-parallel-agents p07-mini-coder p08-kb-rag p09-dms p10-knowledge-platform
     ch26-detagent part11-sutra-erp templates workbench free-tier labs automation/n8n golden-path)
projects=("${@:-${ALL[@]}}")
failed=()
for p in "${projects[@]}"; do
  echo "== $p"
  ( cd "$p"
    [ -d .venv ] || python3 -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    pip install -q -r "${REQ[$p]:-requirements.txt}"
    eval "${CMD[$p]:-python -m pytest -q}" ) || failed+=("$p")
done
if [ ${#failed[@]} -gt 0 ]; then echo "FAILED: ${failed[*]}"; exit 1; fi
echo "All ${#projects[@]} folders passed."
