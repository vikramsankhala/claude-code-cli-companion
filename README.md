# Claude Code CLI: Companion Code

[![Tests](https://github.com/vikramsankhala/claude-code-cli-companion/actions/workflows/tests.yml/badge.svg)](https://github.com/vikramsankhala/claude-code-cli-companion/actions/workflows/tests.yml)
[![Code licence: MIT](https://img.shields.io/badge/code-MIT-0E7C7B.svg)](LICENSE)
[![Book licence: CC BY-NC-SA 4.0](https://img.shields.io/badge/book-CC%20BY--NC--SA%204.0-1F3A5F.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

Tested, runnable code for the hands-on projects in **_Claude Code CLI: The Reference Book and Cheat Sheet_** (second edition, 2026) by **Vikram Singh Sankhala**, Solinexta AI Press.

📖 **Read the book:** [web edition](https://claude.ai/artifact/7ZmwKPUQgXabYtUXmVwEvf)

Every project runs offline, with no model download and no API key, so you can learn the ideas first and connect a real model when you are ready.

---

## What is inside

| Folder | Book | What you build | Tests |
| --- | --- | --- | --- |
| [`p07-mini-coder`](p07-mini-coder) | Project P7, "How Coding Agents Work" | Your own coding agent on an open-source model (Ollama), with tools and safety rules | `python test_agent.py` |
| [`p08-kb-rag`](p08-kb-rag) | Project P8 | Multilingual enterprise knowledge base with hybrid RAG (BM25 + vectors + RRF), access groups and an MCP server | 9 |
| [`p09-dms`](p09-dms) | Project P9 | Multinational document management: regional stores, versions, workflow, retention, legal hold, audit, API | 7 |
| [`p10-knowledge-platform`](p10-knowledge-platform) | Project P10 (capstone) | P8 + P9 as one automated, multilingual knowledge platform with a job queue, connectors, MCP, hooks and a skill | 8 |
| [`ch26-detagent`](ch26-detagent) | Chapter 26 | A deterministic agent: JSON Schema contract, policy in code, state machine, record-and-replay, hash-chained journal | 7 |
| [`part11-sutra-erp`](part11-sutra-erp) | Part XI (Chapters 29–36) | **Sutra**, a next-generation ERP proof of concept: event-sourced ledger, edge alerts, MILP and QUBO optimisation, human-in-the-loop remediation, agent guardrails, statutory and concurrent audit, service desk, system evals | 15 + eval gates |

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
