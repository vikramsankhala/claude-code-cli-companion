# D1 · Orient in a new codebase (10 min)

**Feature:** plan mode, `@` mentions · **Book:** Part X, Guided Demos; Chapters 3 and 5

## Steps

1. Open the practice app copy (see [`../practice-app/README.md`](../practice-app/README.md)) and start Claude Code read-only:
   ```bash
   claude --permission-mode plan
   ```
2. Ask:
   > Map this repo: entry points, data flow, how tests run. Cite files.
3. Then:
   > Explain @shopkeeper/catalogue.py line by line for a new joiner.
4. Finally, point it at the failing tests without letting it edit:
   > Run `python -m pytest exercises -q` in your head from the code: which three tests fail and why? Cite line numbers.

## Observe

- No file can change: plan mode refuses edits and asks before any command.
- Every claim names a file. If one does not, ask "which file says that?"
- It should find all three planted bugs from reading alone. Note how close it gets; you fix them in D2 and D3.

## Codex equivalent

`codex --sandbox read-only --ask-for-approval on-request`, then the same prompts.
