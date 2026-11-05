# One repository, two agents (Chapter 18)

Copy these files into a repository so Claude Code and Codex follow the same rules:

```text
AGENTS.md                 rules for every agent
CLAUDE.md                 imports AGENTS.md, adds Claude-only notes
.claude/settings.json     Claude permissions (deny rules enforce the "Never" list)
.codex/config.toml        Codex sandbox and approvals
.mcp.json                 MCP servers for Claude Code (Codex lists its own in config.toml)
```

Prose asks; configuration enforces. Keep the hard rules in both `.claude/settings.json` and the Codex sandbox.
