# Knowledge Management Platform (KMP)

## What this is
Multilingual knowledge platform: `dms/` is the system of record (regions in, eu, us),
`kb/` is hybrid RAG, `kmp/` wires them with an automated job pipeline.

## Commands
- Tests: `python -m pytest -q`  (offline: set `KB_EMBEDDER=hash`)
- Process inbox and jobs: `python kmp_cli.py run`
- Nightly jobs: `python kmp_cli.py nightly`

## Rules
- Never move data between regions: each region has its own store under `data/stores/<region>/`.
- Only approved, current versions may be indexed for answers.
- Every new job type needs a test in `tests/test_platform.py`.
- Retention values in `dms/config.py` are illustrative; do not change them without a legal ticket.
