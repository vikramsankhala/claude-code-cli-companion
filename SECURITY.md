# Security

## Reporting a vulnerability

Please do **not** open a public issue for a security problem. Email **vikramsankhala@gmail.com** with the subject "Security: claude-code-cli-companion", a description and steps to reproduce. You will get an acknowledgement within five working days.

## Using this code safely

This is teaching code. Before running any of it beyond your own machine:

- **APIs and MCP servers** (`api.py`, `kb_mcp.py`, `kmp_mcp.py`) have no production authentication. Keep them on `localhost`, or put them behind your identity provider and TLS.
- **The coding agent in P7** runs shell commands you approve. Use it on a copy of a repository, never on your home directory.
- **Keys** belong in environment variables or a secrets manager, never in files you commit.
- **Sample users, organisations, tax rates and retention periods** are fictional.
