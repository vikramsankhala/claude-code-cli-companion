# Labs for the eight guided demos

Hands-on material for **Part X · Guided Demos** (D1–D8) of the book. Each demo takes 10–15 minutes and shows one Claude Code feature on a real, small codebase.

| Folder | Demo | Feature | Time |
| --- | --- | --- | --- |
| [`practice-app`](practice-app) | All | **Shopkeeper**, a small shop back end with three planted bugs | — |
| [`d01-orient`](d01-orient) | D1 Orient in a new codebase | Plan mode, `@` mentions | 10 min |
| [`d02-rewind`](d02-rewind) | D2 Rewind a bad edit | Checkpoints, `Esc Esc` | 10 min |
| [`d03-shell-mode`](d03-shell-mode) | D3 Shell-mode feedback loop | `!` prefix, `Ctrl+B` | 10 min |
| [`d04-context-surgery`](d04-context-surgery) | D4 Context surgery | `/context`, `/compact`, `/clear` | 10 min |
| [`d05-parallel-agents`](d05-parallel-agents) | D5 Two agents in parallel | Worktrees, `--bg`, `claude agents` | 15 min |
| [`d06-pipe-and-parse`](d06-pipe-and-parse) | D6 Pipe and parse | `-p`, `--output-format json`, a cost log | 10 min |
| [`d07-guardrail`](d07-guardrail) | D7 Guardrail in five minutes | `PreToolUse` hook, exit `2` (bash and Python versions) | 15 min |
| [`d08-live-tool`](d08-live-tool) | D8 Connect a live tool | `claude mcp add`, `/mcp`, a local MCP server | 15 min |

Answers: [`SOLUTIONS.md`](SOLUTIONS.md).

## Before you start

1. Copy `practice-app` outside this repository and commit it (its README has the commands for bash and PowerShell). Checkpoints, worktrees and diffs need a clean history of their own.
2. You need Claude Code signed in. D1 and D7 also have Codex notes.
3. `pip install -r requirements.txt` is only needed for D8 and the tests.

## Teaching tip

Run D1 → D3 as one 30-minute block: orient read-only, make and rewind a bad edit, then fix the three bugs one per turn. Students see that the safe habits (plan first, small diffs, tests after each change) are also the fast ones.

## Tests

```bash
python -m pytest -q
```

They check that the app's passing tests pass, that exactly three planted failures remain, that both hooks block and allow the right commands, that the D6 parser handles success and error results, that the D8 MCP server answers over stdio, and that every guide's file references exist.
