# Golden path: repository templates

The **5-engineer golden path** from Chapter 24 of the book, as files you copy into a new repository. This repository uses the same set on itself (see [Applied here](#applied-here)).

| File | What it does | Book |
| --- | --- | --- |
| [`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md) | One set of rules for every coding agent; `CLAUDE.md` imports `AGENTS.md` | Chapters 6, 16 |
| [`.claude/settings.json`](.claude/settings.json) | Shared Claude Code permissions (tests and lint allowed, `.env` denied) and a ruff-on-edit hook | Chapters 7–8 |
| [`.codex/config.toml`](.codex/config.toml) | Shared Codex sandbox: workspace-write, network off, approval on request | Chapter 16 |
| [`.pre-commit-config.yaml`](.pre-commit-config.yaml) | File hygiene, ruff lint and format, gitleaks: the same checks on every laptop and in CI | Chapter 24 |
| [`ruff.toml`](ruff.toml) | Strict ruff profile for new code (adds security and simplification rules) | Chapter 24 |
| [`semgrep/rules.yml`](semgrep/rules.yml) | Four project rules: hard-coded keys, `shell=True`, TLS verification off, `eval`/`exec` | Chapter 27 |
| [`renovate.json`](renovate.json) | Weekly grouped dependency updates (Monday before 09:00 IST), majors need approval, actions pinned | Chapter 24 |
| [`.github/dependabot.yml`](.github/dependabot.yml) | The built-in alternative to Renovate. Keep one of the two | Chapter 24 |
| [`.github/CODEOWNERS`](.github/CODEOWNERS) | Platform owns CI and agent rules; security owns Semgrep | Chapter 24 |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | Tests, pre-commit, Semgrep (project + `p/python`) and gitleaks on every pull request | Chapter 24 |
| [`.github/pull_request_template.md`](.github/pull_request_template.md) | Asks whether an agent wrote the change and whether the author read every line | Chapter 28 |
| [`.github/ISSUE_TEMPLATE/bug.yml`](.github/ISSUE_TEMPLATE/bug.yml) | A bug form that reminds people to strip keys from logs | — |

## Use it on a new repository

```bash
cp -r golden-path/. ~/repos/my-service/          # includes the dot-folders
cd ~/repos/my-service
pip install pre-commit && pre-commit install
pre-commit run --all-files
```

```powershell
Copy-Item -Recurse -Force golden-path\* $HOME\repos\my-service\
Copy-Item -Recurse -Force golden-path\.github, golden-path\.claude, golden-path\.codex, golden-path\.pre-commit-config.yaml $HOME\repos\my-service\
cd $HOME\repos\my-service; pip install pre-commit; pre-commit install; pre-commit run --all-files
```

Then: replace `@your-org/...` in `CODEOWNERS`, delete `tests/` and this README, choose Renovate (install the free [Renovate GitHub app](https://github.com/apps/renovate)) **or** Dependabot, and turn on branch protection requiring the CI checks.

Ask an agent to do the fitting for you:

> Adapt the golden-path files to this repository: fill AGENTS.md from the real build and test commands, set CODEOWNERS from git log, and make `pre-commit run --all-files` pass with the smallest changes. Show me the plan first.

## Applied here

| Template | In this repository | Difference |
| --- | --- | --- |
| `.pre-commit-config.yaml` | [`/.pre-commit-config.yaml`](../.pre-commit-config.yaml) | Lint only, no `ruff-format`: the code must stay as printed in the book |
| `ruff.toml` | [`/ruff.toml`](../ruff.toml) | A teaching profile: bug-finding rules on, compact-style rules off |
| `semgrep/rules.yml` | Used directly by [`/.github/workflows/lint.yml`](../.github/workflows/lint.yml) | Registry rules report but do not block |
| `renovate.json` | [`/renovate.json`](../renovate.json) | Identical |
| `CODEOWNERS`, `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json` | At the root and in `.github/` | Written for a multi-project book repository |

## Tests

`python -m pytest -q` checks every file parses, hook versions are pinned and match the root, the Semgrep rules catch each bad example and pass each good one (when Semgrep is installed), and the root still carries the golden path.
