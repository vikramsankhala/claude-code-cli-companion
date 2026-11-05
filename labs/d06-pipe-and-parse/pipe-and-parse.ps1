# D6: summarise the last 30 commits and log the run's cost (Windows PowerShell 5.1 or 7).
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
git log --oneline -30 |
  claude -p "group these commits by theme" --output-format json --max-turns 3 |
  python (Join-Path $here 'parse_result.py') --log (Join-Path $here 'runs.csv')
exit $LASTEXITCODE
