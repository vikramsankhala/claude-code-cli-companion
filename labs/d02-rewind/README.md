# D2 · Rewind a bad edit (10 min)

**Feature:** checkpoints, `Esc Esc` (`/rewind`) · **Book:** Part X, Guided Demos; Chapter 4

## Steps

1. In the practice app, start `claude` (default permission mode).
2. Make a deliberately bad request:
   > Rename every variable in @shopkeeper/pricing.py to single letters.
3. Accept the edit, then run the tests from the prompt: `! python -m pytest -q`
4. Press `Esc Esc` on an empty prompt (or type `/rewind`). Pick the checkpoint **before** the rename and choose **Restore code and conversation**.
5. Check: `! git diff --stat` shows nothing for `pricing.py`.

## Observe

- The file is back exactly as it was, and the conversation has forgotten the bad turn.
- Checkpoints cover Claude's own file edits. They do **not** undo shell side effects (files a command deleted, a migration it ran). Git is still your real safety net, which is why the practice app starts with a commit.

Official: [Checkpointing](https://code.claude.com/docs/en/checkpointing)
