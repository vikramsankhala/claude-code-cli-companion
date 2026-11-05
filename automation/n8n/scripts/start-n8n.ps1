# Run n8n with npm on this machine so Execute Command can reach claude and codex. Localhost only.
$ErrorActionPreference = 'Stop'
if (-not (Get-Command n8n -ErrorAction SilentlyContinue)) { Write-Host 'Install first: npm install -g n8n'; exit 1 }
foreach ($c in 'claude', 'codex') {
  if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { Write-Host "note: $c not on PATH; workflows that call it will fail" }
}
$env:N8N_HOST = '127.0.0.1'
$env:N8N_LISTEN_ADDRESS = '127.0.0.1'
$env:N8N_PORT = '5678'
$env:NODES_EXCLUDE = '[]'                        # re-enables Execute Command: trusted machines only
$env:N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS = 'true'
if (-not $env:GENERIC_TIMEZONE) { $env:GENERIC_TIMEZONE = 'Asia/Kolkata' }
n8n start
