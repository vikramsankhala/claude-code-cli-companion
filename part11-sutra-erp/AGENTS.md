# Sutra ERP: rules for coding agents (Claude Code, Codex, Vibe, OpenCode)

## Commands
- Test: `python -m pytest -q` (offline; sets KB_EMBEDDER=hash)
- System evals: `KB_EMBEDDER=hash python -m sutra.evals` (all gates must pass)
- Demo: `python demo.py` · API: `KB_EMBEDDER=hash uvicorn api:app --reload`

## Architecture in one breath
Events are the source of truth (`sutra/events.py`, append-only, hash-chained). Ledger, audit, helpdesk
and remediation read events. Every agent action passes `Guard.check` first. Country rules live in `packs/*.yaml`.

## Never
- Never write to the `events` table except through `EventStore.append`.
- Never let an agent call `stop_asset` or post payments without `approved_by`.
- Never hard-code a tax rate or retention period in Python; add it to a country pack.
- Never weaken a gate in `sutra/evals.py` to make a change pass.
