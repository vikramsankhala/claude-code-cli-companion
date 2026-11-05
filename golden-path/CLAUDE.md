@AGENTS.md

## Claude Code specifics
- Use plan mode for anything touching more than three files.
- The hooks in `.claude/settings.json` run ruff on edited Python files; fix what they report before moving on.
