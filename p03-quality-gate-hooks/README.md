# P3 · Quality-gate hooks

Book: Project P3 (Part X), building on Chapter 8.

**Goal.** Every edit is formatted, every turn ends with green tests, and dangerous commands never run.

| Event | Hook | What it does |
| --- | --- | --- |
| `PostToolUse` on `Edit\|Write` | `format_file.py` | Runs `ruff format` and `ruff check --fix` on the edited file |
| `PreToolUse` on `Bash` | `guard_bash.py` | Exit 2 (block) on `rm -rf` of root or home, and on any force push |
| `Stop` | `stop_tests.py` | Runs the fast tests; on failure returns `decision: "block"` with the summary, and respects `stop_hook_active` so it cannot loop |
| `SessionStart` | `session_context.py` | Adds the current branch and open TODOs as `additionalContext` |

The hooks are Python, so the same files work on Windows, macOS and Linux. On Windows, Claude Code runs hook commands through Git Bash, so `$CLAUDE_PROJECT_DIR` expands as shown.

## Do it

1. Copy `solution/.claude/` into your copy of `sample-app` (or write your own first).
2. Run `/hooks` in Claude Code to confirm all four are registered.
3. Ask Claude to "force-push to main" and watch it refused; break a test and watch Claude keep working until it passes.
4. Run `claude --debug "hooks"` and save a log excerpt showing one block.

## Test the hooks without Claude

```bash
pip install -r requirements.txt
python -m pytest -q      # feeds each hook the JSON Claude Code sends and checks the result
```
