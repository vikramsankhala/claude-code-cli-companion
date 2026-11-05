# D6 · Pipe and parse (10 min)

**Feature:** `-p`, `--output-format json`, `jq` · **Book:** Part X, Guided Demos; Chapter 11

## Steps

From inside any git repository:

```bash
git log --oneline -30 | claude -p "group these commits by theme" --output-format json | jq -r '.result, .total_cost_usd'
```

No `jq`? Use the Python parser here, which also appends a line to a cost log:

```bash
git log --oneline -30 | claude -p "group these commits by theme" --output-format json | python parse_result.py --log runs.csv
```

```powershell
git log --oneline -30 | claude -p "group these commits by theme" --output-format json | python parse_result.py --log runs.csv
```

Or run the wrapper: `./pipe-and-parse.sh` (macOS, Linux, Git Bash) or `.\pipe-and-parse.ps1` (PowerShell).

Try the parser without Claude Code at all: `python parse_result.py < sample-result.json`.

## Observe

- `.result` is the text; `.total_cost_usd`, `.num_turns` and `.duration_ms` are what a script logs.
- `.is_error` is `true` when the run failed (for example `--max-turns` was reached); `parse_result.py` exits 1 then, so a CI step fails loudly.
- On a subscription plan the cost field is an estimate, not a bill.
