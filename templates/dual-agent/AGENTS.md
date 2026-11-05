# Rules for every coding agent (Codex reads this file; Claude Code imports it)

## Commands
- Test: `python -m pytest -q`
- Lint and format: `ruff check --fix .` then `ruff format .`

## Conventions
- Small, reviewed changes; a test with every behaviour change.
- British English in comments, messages and docs.

## Never
- Never read `.env*` or `secrets/`.
- Never push to `main`; never force-push.
- Never weaken a test or a CI gate to make a change pass.
