# D3 · Shell-mode feedback loop (10 min)

**Feature:** `!` prefix, `Ctrl+B` to background · **Book:** Part X, Guided Demos; Chapter 4

## Steps

1. In the practice app, inside `claude`, type:
   ```text
   ! python -m pytest exercises -q
   ```
   The three failures land in the conversation without a tool call.
2. Ask:
   > Fix the first failing test only. Do not touch exercises/.
3. Re-run `! python -m pytest exercises -q`: two left. Repeat until none are left, one bug per turn.
4. Start the API and push it to the background:
   ```text
   ! python -m shopkeeper.server
   ```
   then press `Ctrl+B`. Ask: "Fetch http://127.0.0.1:8765/items?page=1 and check it now starts with TEA-250."

## Observe

- `!` output enters context cheaply; Claude reads it as if it ran the command itself.
- One bug per turn keeps every diff small enough to review.
- The backgrounded server keeps running while you work; `/tasks` (or the task list) shows it.
