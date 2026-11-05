# P2 · Safe permissions baseline

Book: Project P2 (Part X), building on Chapter 7.

**Goal.** Remove routine prompts without opening risky doors.

## Do it

1. In your copy of `sample-app`, write `.claude/settings.json` that allows the lint, test and run commands.
2. Put `git push *` and package installs in `ask`; deny reads of `.env*` and `secrets/**`.
3. Add the `$schema` line, then run `/status` and `claude doctor` to confirm it loads.
4. Create a `.env` from `.env.example` and ask Claude to read it. Record the refusal.
5. Run `/fewer-permission-prompts` and decide which suggestions to accept.
6. Write one sentence per deny rule explaining why it exists.

## Check your work

```bash
python check.py /path/to/your/practice/repo/.claude/settings.json
```

The script prints how six sample tool calls would be decided, using a simplified model of Claude Code's rules (deny beats ask beats allow), then checks the baseline. `solution/` holds a reference `settings.json` and `RATIONALE.md`.
