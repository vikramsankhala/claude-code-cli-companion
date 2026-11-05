# Chapter 42 and Chapter 43, week 6 review: copy work to a backup drive, skipping rebuildable folders.
# Change $Dest to your USB drive or second disk. Schedule nightly with:
#   schtasks /create /sc daily /st 21:00 /tn "WorkBackup" /tr "powershell -NoProfile -ExecutionPolicy Bypass -File $HOME\work\scripts\backup.ps1"
param(
    [string]$Source = (Join-Path $HOME "work"),
    [string]$Dest   = "E:\Backup\work"
)
$log = Join-Path $Source "scripts\backup.log"
robocopy $Source $Dest /E /XD .venv __pycache__ .pytest_cache node_modules /R:1 /W:1 /NP "/LOG+:$log"
# robocopy exit codes 0 to 7 mean success; 8 or more means at least one failure
if ($LASTEXITCODE -ge 8) { Write-Error "Backup failed with robocopy code $LASTEXITCODE"; exit 1 }
Write-Output "Backup finished: $Source -> $Dest (robocopy code $LASTEXITCODE)"
exit 0
