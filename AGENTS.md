# AGENTS.md: rules for coding agents working on this repository

This repository is the companion code for a book. Every folder is a separate project with its own `requirements.txt` and tests.

## Commands
- Test one folder: `cd <folder> && python -m pytest -q` (see `scripts/test-all.sh` for the three folders with special commands).
- Test everything: `./scripts/test-all.sh` or `.\scripts\test-all.ps1`.
- Lint: `pre-commit run --all-files` (ruff, gitleaks, file hygiene). Semgrep project rules: `semgrep scan --config golden-path/semgrep/rules.yml`.

## Rules
- Keep code as printed in the book: no reformatting, no renames, no style-only changes. Fix bugs with the smallest diff and a test.
- Every project must stay offline by default: no test may need a network, a model download or an API key.
- Never commit keys. Labs read them from environment variables; `.env` is git-ignored.
- `labs/practice-app` contains three bugs on purpose. Do not fix them; `labs/tests` checks they are still there.
- A new folder needs a README row, an entry in `scripts/test-all.sh`, `scripts/test-all.ps1` and the CI matrix in `.github/workflows/tests.yml`.
- British spelling in prose.
