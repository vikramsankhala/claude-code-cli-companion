# P10 · Capstone: an automated, multilingual knowledge platform

Book: Project P10.

P8 and P9 joined into one platform: files dropped in `inbox/` are classified, registered, reviewed, published to the regional knowledge base and kept in step by a job queue. Connectors pull from external SQL databases and HTTP JSON sources with watermarks; a nightly job reconciles indexes, applies retention and writes a knowledge-gap report.

```bash
pip install -r requirements.txt
python -m pytest -q                       # 8 passed (sets KB_EMBEDDER=hash itself)

export KB_EMBEDDER=hash                   # PowerShell: $env:KB_EMBEDDER = "hash"
python kmp_cli.py run                     # process the inbox
python kmp_cli.py approve <doc_id>
python kmp_cli.py ask "What is the notice period in India?"
python kmp_cli.py nightly
claude mcp add --transport stdio kmp -- python kmp_mcp.py
```

Copy `sources.example.json` to `sources.json` and edit it before `python kmp_cli.py sync`.

**Agent and CI files**

- `CLAUDE.md`, `.claude/settings.json`, `.claude/hooks/run-tests.sh` and `.claude/skills/kb-gap-writer/` are used by Claude Code when you open this folder.
- `ci-examples/workflows/ci.yml` and `nightly.yml` are GitHub Actions workflows. GitHub only runs workflows from the repository root, so copy them to `.github/workflows/` in your own repository to use them.
