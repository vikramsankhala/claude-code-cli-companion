# Review a pull request and fail when the risk is high.   Usage: .\scripts\review.ps1 -PR 42
param([Parameter(Mandatory)][int]$PR)
$ErrorActionPreference = "Stop"
$here = Split-Path $PSScriptRoot -Parent
$schema = Get-Content "$here\schema\review.schema.json" -Raw
gh pr diff $PR | claude --bare -p "Review this pull request diff for bugs, security problems and missing tests. Report only real issues." `
  --output-format json --json-schema $schema --max-turns 8 --max-budget-usd 1 |
  Out-File review.json -Encoding utf8
python "$here\scripts\gate.py" review.json
exit $LASTEXITCODE
