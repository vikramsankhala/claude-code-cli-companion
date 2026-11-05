# Run every project's tests in its own virtual environment (Windows PowerShell).
# Usage: .\scripts\test-all.ps1            all folders
#        .\scripts\test-all.ps1 p03-quality-gate-hooks workbench
# If blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
param([string[]]$Only)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$env:KB_EMBEDDER = "hash"; $env:PYTHONUTF8 = "1"; $env:MPLBACKEND = "Agg"
$all = @("sample-app", "p01-project-memory", "p02-permissions-baseline", "p03-quality-gate-hooks", "p04-skills-agents-kit",
         "p05-ci-reviewer", "p06-parallel-agents", "p07-mini-coder", "p08-kb-rag", "p09-dms", "p10-knowledge-platform",
         "ch26-detagent", "part11-sutra-erp", "templates", "workbench", "free-tier", "labs", "automation/n8n", "golden-path")
$cmd = @{
  "p07-mini-coder"   = @("python test_agent.py", "python test_agent_extended.py")
  "part11-sutra-erp" = @("python -m pytest -q", "python -m sutra.evals")
  "workbench"        = @("python -m pytest -q tests practice/fintech")
}
$req = @{ "workbench" = "requirements-ci.txt" }
$projects = if ($Only) { $Only } else { $all }
$failed = @()
foreach ($p in $projects) {
  Write-Host "== $p"
  Push-Location $p
  try {
    if (-not (Test-Path .venv)) { python -m venv .venv }
    & .\.venv\Scripts\Activate.ps1
    $r = if ($req.ContainsKey($p)) { $req[$p] } else { "requirements.txt" }
    python -m pip install -q -r $r
    $steps = if ($cmd.ContainsKey($p)) { $cmd[$p] } else { @("python -m pytest -q") }
    foreach ($c in $steps) {
      Invoke-Expression $c | Out-Host
      if ($LASTEXITCODE -ne 0) { throw "$c failed" }
    }
  } catch { $failed += $p } finally {
    if (Get-Command deactivate -ErrorAction SilentlyContinue) { deactivate }
    Pop-Location
  }
}
if ($failed.Count) { Write-Host "FAILED: $($failed -join ', ')"; exit 1 }
Write-Host "All $($projects.Count) folders passed."
