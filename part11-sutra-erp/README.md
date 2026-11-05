# Part XI · Sutra: a next-generation ERP proof of concept

Book: Part XI, Chapters 30 to 37.

| Module | File | What it proves |
| --- | --- | --- |
| Event store | `sutra/events.py` | Append-only, hash-chained events; tampering is detected |
| Compliance packs | `packs/*.yaml`, `sutra/compliance.py` | Country rules as validated configuration (IN, DE, US samples) |
| Ledger | `sutra/ledger.py` | Double entry; unbalanced journals are refused |
| Edge monitoring | `sutra/iot.py` | Threshold, predictive and anomaly alerts with cooldown |
| Optimisation | `sutra/optimize.py` | MILP production plan (HiGHS via SciPy); QUBO maintenance schedule with a local annealer and quantum-provider adapters |
| Remediation | `sutra/remediate.py` | Confidence and risk route proposals to auto, approve or escalate |
| Guardrails | `sutra/guard.py` | Agent allowlists, approvers, limits, suspension, PII redaction, agent monitor |
| Audit | `sutra/audit.py` | Statutory tests (integrity, journal-entry tests, Benford, MUS) and concurrent controls |
| Service desk | `sutra/helpdesk.py`, `kbdocs/` | Ticket retrieval, ranked root causes with confidence, suggested fixes |
| Configuration advisor | `sutra/config_advisor.py` | Finds tax, approval and residency mistakes and offers fixes |
| System evals | `sutra/synth.py`, `sutra/evals.py` | Synthetic data and seven release gates |

```bash
pip install -r requirements.txt
python -m pytest -q                                   # 15 passed
KB_EMBEDDER=hash python -m sutra.evals                # every gate true
python demo.py                                        # the investor demo
KB_EMBEDDER=hash uvicorn api:app --reload             # http://localhost:8000/docs
```

**Also here**

- `schema/sutra.sql`: the production schema for PostgreSQL 16 with TimescaleDB and pgvector (reference; the proof of concept uses SQLite).
- `AGENTS.md`, `CLAUDE.md`, `.claude/` and `.codex/`: one repository set up for both Claude Code and Codex.
- `n8n/nightly-evals.json`: import into n8n with `n8n import:workflow --input=n8n/nightly-evals.json`.

Tax rates, approval limits and organisations are fictional. Quantum adapters need the vendor SDK and credentials; without them the local annealer is used.
