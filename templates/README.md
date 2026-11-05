# templates · copy-ready configuration

Every configuration file the book teaches, ready to copy and edit. All of them are checked by `tests/` (they parse, and the safety rules are present).

| Folder | Files | Book |
| --- | --- | --- |
| `claude/` | `CLAUDE.md` template, a path-scoped rule in `rules/` | Chapter 6 |
| `claude/settings/` | `starter.json`, `team.json`, `strict.json` permission baselines; `hooks.json` wiring | Chapters 7, 8 |
| `claude/hooks/` | Format-on-edit, Bash guard, tests-on-stop and session-context hooks (Python, cross-platform) | Chapter 8 |
| `claude/mcp.json` | `.mcp.json` with `${VAR}` and `${VAR:-default}` expansion; HTTP and stdio servers | Chapter 9 |
| `claude/skills/`, `claude/agents/` | A read-only skill and a review subagent | Chapter 10 |
| `codex/` | User `config.toml`, project `.codex/config.toml`, a CI profile | Chapter 16 |
| `github/` | `@claude` workflow (`claude-code-action`) and Codex PR review (`codex-action`) | Chapters 11, 16 |
| `dual-agent/` | One repository set up for Claude Code and Codex together | Chapter 18 |
| `fde/` | Deployment brief, evaluation sheet, weekly status, handover checklist and field note for forward deployed engineers | Chapter 29 |

**Where each file goes**

| Template | Copy to |
| --- | --- |
| `claude/CLAUDE.md` | repository root |
| `claude/settings/team.json` | `.claude/settings.json` |
| `claude/settings/starter.json` | `~/.claude/settings.json` (personal) |
| `claude/hooks/*.py` + `claude/settings/hooks.json` | `.claude/hooks/` and merge the `hooks` block into `.claude/settings.json` |
| `claude/mcp.json` | `.mcp.json` at the repository root |
| `claude/skills/<name>/` | `.claude/skills/<name>/` or `~/.claude/skills/<name>/` |
| `claude/agents/<name>.md` | `.claude/agents/` or `~/.claude/agents/` |
| `codex/config.toml` | `~/.codex/config.toml` |
| `codex/project-config.toml` | `.codex/config.toml` |
| `github/*.yml` | `.github/workflows/` |

Settings files are strict JSON: no comments and no trailing commas. Add secrets as environment variables or CI secrets, never in these files.
