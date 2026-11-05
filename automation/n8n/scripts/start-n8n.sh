#!/usr/bin/env bash
# Run n8n with npm on this machine so Execute Command can reach claude and codex. Localhost only.
set -euo pipefail
command -v n8n > /dev/null || { echo "Install first: npm install -g n8n"; exit 1; }
for c in claude codex; do command -v "$c" > /dev/null || echo "note: $c not on PATH; workflows that call it will fail"; done
export N8N_HOST=127.0.0.1 N8N_LISTEN_ADDRESS=127.0.0.1 N8N_PORT=5678
export NODES_EXCLUDE="[]"                       # re-enables Execute Command: trusted machines only
export N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true
export GENERIC_TIMEZONE="${GENERIC_TIMEZONE:-Asia/Kolkata}"
exec n8n start
