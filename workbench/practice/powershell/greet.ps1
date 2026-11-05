# Chapter 43: a script with an input. Run: .\greet.ps1 -Name Asha
param([string]$Name = "World")
$time = Get-Date -Format "HH:mm"
Write-Output "Hello, $Name. It's $time."
