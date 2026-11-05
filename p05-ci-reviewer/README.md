# P5 · CI reviewer with structured output

Book: Project P5 (Part X), building on Chapter 11.

**Goal.** Every pull request gets a machine-readable risk report, and high-risk changes fail the check.

| File | Purpose |
| --- | --- |
| `schema/review.schema.json` | `risk` (low, medium, high), `summary`, `findings[]` with `file`, `line`, `issue`, `fix` |
| `scripts/review.sh` · `scripts/review.ps1` | `gh pr diff` piped to `claude --bare -p --output-format json --json-schema …` with turn and budget caps |
| `scripts/gate.py` | Validates `.structured_output`, writes a Markdown summary, exits 1 on high risk and 2 if the report is missing |
| `ci-examples/claude-review.yml` | The gate as a GitHub Actions job: secrets only, read-only permissions, a timeout |
| `ci-examples/claude-review-action.yml` | The same review via `anthropics/claude-code-action@v1`, posted as a PR comment |
| `samples/` | Example results for testing the gate without calling Claude |

## Run it on a real pull request

```bash
export ANTHROPIC_API_KEY=...            # PowerShell: $env:ANTHROPIC_API_KEY = "..."
scripts/review.sh 42                    # PowerShell: .\scripts\review.ps1 -PR 42
```

`--bare` gives repeatable CI runs and needs an API key rather than a subscription login (Chapter 11).

## Test the gate offline

```bash
pip install -r requirements.txt
python -m pytest -q
```
