# Chapter 42 and Chapter 44, day 6: one-word shortcuts for your PowerShell profile.
# Open your profile with: notepad $PROFILE   then paste what you need and open a new window.
# Change the paths if your folders live elsewhere.

$Work     = Join-Path $HOME "work"
$Research = Join-Path $HOME "research"

function work     { Set-Location $Work; & (Join-Path $Work ".venv\Scripts\Activate.ps1") }
function research { Set-Location $Research; & (Join-Path $Research ".venv\Scripts\Activate.ps1") }
function books    { work; Set-Location books }
function where-am-i {
    "Folder : $(Get-Location)"
    "Python : $((Get-Command python -ErrorAction SilentlyContinue).Source)"
    "Venv   : $env:VIRTUAL_ENV"
}

# Week 4 review: your start-of-day routine. Set the project you are working on.
function today {
    work
    Set-Location (Join-Path $Work "apps\emi-app")
    git status
    claude -c
}

# Week 5 review: run the network check script from anywhere.
function netcheck { & (Join-Path $Work "scripts\netcheck.ps1") }
