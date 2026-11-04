# Run every project's tests in its own virtual environment (Windows PowerShell).
# Usage: .\scripts\test-all.ps1   (if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned)
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$env:KB_EMBEDDER = "hash"
$projects = [ordered]@{
  "p07-mini-coder"         = @("python test_agent.py")
  "p08-kb-rag"             = @("python -m pytest -q")
  "p09-dms"                = @("python -m pytest -q")
  "p10-knowledge-platform" = @("python -m pytest -q")
  "ch26-detagent"          = @("python -m pytest -q")
  "part11-sutra-erp"       = @("python -m pytest -q", "python -m sutra.evals")
}
$failed = @()
foreach ($p in $projects.Keys) {
  Write-Host "== $p"
  Push-Location $p
  try {
    if (-not (Test-Path .venv)) { python -m venv .venv }
    & .\.venv\Scripts\Activate.ps1
    python -m pip install -q -r requirements.txt
    foreach ($c in $projects[$p]) {
      Invoke-Expression $c | Out-Host
      if ($LASTEXITCODE -ne 0) { throw "$c failed" }
    }
  } catch { $failed += $p } finally { if (Get-Command deactivate -ErrorAction SilentlyContinue) { deactivate }; Pop-Location }
}
if ($failed.Count) { Write-Host "FAILED: $($failed -join ', ')"; exit 1 }
Write-Host "All projects passed."
