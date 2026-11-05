# AGENTS.md: rules for every coding agent (Codex, Claude Code via CLAUDE.md, others)

## Project
- Python 3.11+. Install: `pip install -r requirements.txt`. Test: `python -m pytest -q`. Lint: `pre-commit run --all-files`.

## Rules
- Small diffs. One concern per pull request. Run the tests after every change.
- Never commit secrets. Read keys from environment variables; `.env` is git-ignored.
- Do not edit `.github/`, `semgrep/` or this file unless the task says so: CODEOWNERS will ask for platform review.
- New code needs a test. A bug fix needs a test that failed before the fix.
- Ask before adding a dependency; say why and what it costs.
