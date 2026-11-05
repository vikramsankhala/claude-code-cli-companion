# D7 · Guardrail in five minutes (15 min)

**Feature:** `PreToolUse` hook, exit code `2` · **Book:** Part X, Guided Demos; Chapter 8

Two versions of the same hook are here:

| File | Needs | Use on |
| --- | --- | --- |
| `.claude/hooks/block-rm.sh` | bash and `jq` | macOS, Linux (the Chapter 8 listing, unchanged) |
| `.claude/hooks/block_rm.py` | Python | Everywhere, including Windows; also catches `-fr`, `-Rf` and `--recursive --force` |

`.claude/settings.json` registers the Python one. To use the bash one instead, copy `settings.bash-variant.json` over it.

## Steps

1. Test the hook **without** Claude Code first: `./try-hook.sh` or `.\try-hook.ps1`. Expect exit `0`, `2`, `0`.
2. Copy `.claude/` into the practice app (or any scratch repository):
   ```bash
   cp -r labs/d07-guardrail/.claude ~/shopkeeper/
   ```
   ```powershell
   Copy-Item -Recurse labs\d07-guardrail\.claude $HOME\shopkeeper\
   ```
3. Start `claude` there and run `/hooks`: the `PreToolUse` · `Bash` entry is listed.
4. Ask:
   > Clean up by running rm -rf ~/tmp-test
5. Ask for something harmless: "run rm -rf ./build" (allowed: it is inside the project).

## Observe

- The dangerous call is blocked **before** it runs, and Claude reads the reason from stderr and tells you.
- Exit `1` would only warn; exit `2` blocks. Deny rules in settings still apply whatever a hook returns.
- A hook is a speed bump, not a sandbox: a determined command can be phrased around a regex. Pair it with permissions (Chapter 7) and, for untrusted work, a sandbox.
