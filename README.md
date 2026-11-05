# Claude Code CLI: Companion Code

[![Tests](https://github.com/vikramsankhala/claude-code-cli-companion/actions/workflows/tests.yml/badge.svg)](https://github.com/vikramsankhala/claude-code-cli-companion/actions/workflows/tests.yml)
[![Lint](https://github.com/vikramsankhala/claude-code-cli-companion/actions/workflows/lint.yml/badge.svg)](https://github.com/vikramsankhala/claude-code-cli-companion/actions/workflows/lint.yml)
[![Code licence: MIT](https://img.shields.io/badge/code-MIT-0E7C7B.svg)](LICENSE)
[![Book licence: CC BY-NC-SA 4.0](https://img.shields.io/badge/book-CC%20BY--NC--SA%204.0-1F3A5F.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

Tested, runnable code for the hands-on projects in **_Claude Code CLI: The Reference Book and Cheat Sheet_** (second edition, 2026) by **Vikram Singh Sankhala**, Solinexta AI Press.

📖 **Read the book:** [web edition](https://claude.ai/artifact/7ZmwKPUQgXabYtUXmVwEvf)

Every project runs offline, with no model download and no API key, so you can learn the ideas first and connect a real model when you are ready. Continuous integration runs every folder on Windows and Linux, lints with pre-commit and Semgrep, and runs Sutra against real PostgreSQL and MQTT services.

---

## What is inside

**Projects from the book**

| Folder | Book | What you build | Tests |
| --- | --- | --- | --- |
| [`sample-app`](sample-app) | Projects P1–P6 | The small practice repository the first six projects work on | 3 |
| [`p01-project-memory`](p01-project-memory) | Project P1, Chapter 6 | A team-ready `CLAUDE.md`, path-scoped rules and a checker | 2 |
| [`p02-permissions-baseline`](p02-permissions-baseline) | Project P2, Chapter 7 | A safe permissions baseline with its rationale | 3 |
| [`p03-quality-gate-hooks`](p03-quality-gate-hooks) | Project P3, Chapter 8 | Format-on-edit, Bash guard, tests-on-stop and session-context hooks | 15 |
| [`p04-skills-agents-kit`](p04-skills-agents-kit) | Project P4, Chapter 10 | Two skills, a subagent and a plugin manifest | 2 |
| [`p05-ci-reviewer`](p05-ci-reviewer) | Project P5, Chapter 11 | A CI reviewer with a JSON Schema, a gate script and GitHub Actions workflows | 5 |
| [`p06-parallel-agents`](p06-parallel-agents) | Project P6, Chapter 12 | Plan, split and run parallel agents in worktrees, with a plan checker | 4 |
| [`p07-mini-coder`](p07-mini-coder) | Project P7, "How Coding Agents Work" | Your own coding agent on an open-source model (Ollama), with tools and safety rules | 2 scripts |
| [`p08-kb-rag`](p08-kb-rag) | Project P8 | Multilingual enterprise knowledge base with hybrid RAG (BM25 + vectors + RRF), access groups and an MCP server | 9 |
| [`p09-dms`](p09-dms) | Project P9 | Multinational document management: regional stores, versions, workflow, retention, legal hold, audit, API | 7 |
| [`p10-knowledge-platform`](p10-knowledge-platform) | Project P10 (capstone) | P8 + P9 as one automated, multilingual knowledge platform | 8 |
| [`ch26-detagent`](ch26-detagent) | Chapter 26 | A deterministic agent: schema contract, policy in code, state machine, record-and-replay, hash-chained journal | 7 |
| [`part11-sutra-erp`](part11-sutra-erp) | Part XI (Chapters 30–37) | **Sutra**, a next-generation ERP proof of concept, with a working Qiskit QAOA adapter, an MQTT edge simulator and a Docker database (TimescaleDB + pgvector, Mosquitto) | 28 + 2 integration + eval gates |

**Hands-on labs and automation**

| Folder | Book | What it holds | Tests |
| --- | --- | --- | --- |
| [`labs`](labs) | Part X, Guided Demos D1–D8 | A practice app with three planted bugs, a guide per demo, the D7 hook (bash and Python), the D6 cost-logging parser and a D8 MCP server | 22 |
| [`automation/n8n`](automation/n8n) | Chapters 19–20 | Four importable n8n workflows, one per integration pattern (CI summary, issue triage, morning brief, agent tools over MCP), and start scripts | 23 |

**Reference material**

| Folder | Book | What it holds | Tests |
| --- | --- | --- | --- |
| [`templates`](templates) | Chapters 6–11, 16, 18, 29 | Copy-ready `CLAUDE.md`, settings at three strictness levels, hooks, `.mcp.json`, a skill, a subagent, Codex configs, GitHub workflows, a dual-agent repository and five forward-deployed-engineer templates | 9 |
| [`free-tier`](free-tier) | Chapter 22 | NVIDIA API catalogue labs (first call, model comparison, embeddings, tools, safety), the **free-tier gateway kit** (a LiteLLM gateway across NVIDIA, OpenRouter, Groq, Gemini and Mistral free tiers), key checks, and an educator guide with lesson plans, student set-up and an acceptable-use template. **Teaching and prototyping only** | 10 |
| [`golden-path`](golden-path) | Chapter 24 | Repository templates for the 5-engineer golden path: pre-commit, ruff, Semgrep rules, Renovate, CODEOWNERS, CI, agent settings. **Applied to this repository** | 8 |
| [`workbench`](workbench) | Part XII (Chapters 38–44) | Every Python package example from Chapters 39–40, and the six-week practice files (EMI calculator, PowerShell profile, network check, backup) | 27 |

## Quick start

You need **Python 3.11 or later** and **git**.

**Windows (PowerShell)**

```powershell
git clone https://github.com/vikramsankhala/claude-code-cli-companion.git
cd claude-code-cli-companion
.\scripts\test-all.ps1            # creates one virtual environment per project and runs every test
```

**macOS and Linux**

```bash
git clone https://github.com/vikramsankhala/claude-code-cli-companion.git
cd claude-code-cli-companion
./scripts/test-all.sh
```

To test only some folders, name them: `.\scripts\test-all.ps1 p03-quality-gate-hooks workbench`.

**Lint like CI does** (the golden path, applied here):

```bash
pip install pre-commit
pre-commit install          # checks run before every commit from now on
pre-commit run --all-files
```

**One project at a time**

```bash
cd part11-sutra-erp
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -q
python demo.py                                         # the five-minute investor demo
```

## Offline by default, real models when you want them

| Setting | Offline (default in tests) | With a real model |
| --- | --- | --- |
| Embeddings (P8, P10, Sutra) | `KB_EMBEDDER=hash` | Run Ollama and `ollama pull bge-m3`; unset `KB_EMBEDDER` |
| Answers (P8, P10) | Retrieval only (`search`) | `ask` uses `KB_CHAT_MODEL` (default `qwen3:8b`) at `KB_BASE_URL` (default Ollama) |
| Agent model (P7) | Fake server inside the test | `ollama pull qwen3:8b` (or set `MINI_CODER_MODEL` to another tool-calling model), then `python agent.py` |
| Extraction (detagent) | Replays `cassettes/` | `python run.py invoice.txt --record <model>` against any OpenAI-compatible endpoint |

Free hosted endpoints that work here are covered in Chapter 22 of the book.

## Working on this code with coding agents

Each larger project carries the rules files described in the book:

- `CLAUDE.md` and `.claude/settings.json` (permissions and hooks) for **Claude Code**
- `AGENTS.md` for **Codex** and other agents; `CLAUDE.md` imports it with `@AGENTS.md`
- `.codex/config.toml` in Sutra: workspace sandbox with the network off
- `p10-knowledge-platform/ci-examples/` and `part11-sutra-erp/n8n/`: CI workflows and an n8n workflow to copy into your own setup

Open a project folder in VS Code with the Claude Code or Codex extension, or run `claude` or `codex` in it.

## Safety

- These projects are teaching code. Read [SECURITY.md](SECURITY.md) before you expose an API or MCP server beyond your own machine.
- Never commit API keys; `.gitignore` excludes `.env` files and local databases.
- Tax rates, retention periods and every organisation in the samples are fictional.

## Licence

- **Code** in this repository: [MIT](LICENSE). Use it freely, including commercially; keep the notice.
- **The book** is separate and licensed [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). See [NOTICE.md](NOTICE.md).

## Cite

See [CITATION.cff](CITATION.cff), or:

> Sankhala, V. S. (2026). *Claude Code CLI: The Reference Book and Cheat Sheet* (2nd ed.). Solinexta AI Press. Companion code: github.com/vikramsankhala/claude-code-cli-companion.

## Author

**Vikram Singh Sankhala**, Founder, Solinexta AI · B.Tech IIT Kharagpur · MBA IIM Calcutta · IRS · FRM

[solinexta-ai.org](https://solinexta-ai.org) · [LinkedIn](https://www.linkedin.com/in/vikramsankhalaai) · [GitHub](https://github.com/vikramsankhala)

Found a bug or a broken step in the book? [Open an issue](../../issues). Contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md).
