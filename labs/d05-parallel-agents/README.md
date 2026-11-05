# D5 · Two agents in parallel (15 min)

**Feature:** worktrees (`-w`), background sessions (`--bg`), `claude agents` · **Book:** Part X, Guided Demos; Chapter 12

## Steps

The practice app must be a git repository with at least one commit (see its README).

```bash
claude -w add-health --bg "add a GET /health endpoint to shopkeeper/server.py returning {\"status\": \"ok\"}, with a test"
claude -w docs-pass --bg "improve the README setup instructions for Windows and macOS"
claude agents
```

When both finish, review and merge each branch:

```bash
git worktree list
git diff main...add-health
git merge add-health && git merge docs-pass
python -m pytest -q
git worktree remove .claude/worktrees/add-health
git worktree remove .claude/worktrees/docs-pass
```

The same flow without the flags, in two terminals, is in [`walkthrough.sh`](walkthrough.sh).

## Observe

- Two isolated branches under `.claude/worktrees/`; neither agent sees the other's edits, so there are no conflicts.
- `claude agents` shows both sessions and their state. Attach to one to answer a question it is waiting on.
- Each worktree needs its own virtual environment if the project has dependencies (Shopkeeper has none).

Official: [Worktrees](https://code.claude.com/docs/en/worktrees) · [Agent view](https://code.claude.com/docs/en/agent-view)
