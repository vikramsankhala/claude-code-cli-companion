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
| Quantum (gate model) | `sutra/qaoa.py` | A working QAOA adapter on Qiskit: QUBO to Ising, tuned circuit, sampled answer checked against brute force |
| Edge over MQTT | `sutra/mqtt_edge.py` | Simulated sensors, an edge gateway that publishes only alerts, in memory or over a real broker |
| Database | `docker-compose.yml`, `schema/apply.py` | The production schema in TimescaleDB + pgvector, plus a Mosquitto broker |

```bash
pip install -r requirements.txt
python -m pytest -q                                   # 28 passed, 2 skipped (they need the services below)
KB_EMBEDDER=hash python -m sutra.evals                # every gate true
python demo.py                                        # the investor demo
KB_EMBEDDER=hash uvicorn api:app --reload             # http://localhost:8000/docs
```

**Extras: real services on your laptop** (needs Docker Desktop)

```bash
docker compose up -d --wait                           # TimescaleDB + pgvector on 5432, Mosquitto on 1883
pip install -r requirements-extras.txt
python schema/apply.py --check                        # the schema loaded on first start: 30 tables, a hypertable
SUTRA_MQTT_HOST=localhost SUTRA_PG_DSN=postgresql://sutra:sutra@localhost:5432/sutra SUTRA_PG_FULL=1 \
  python -m pytest -q tests/test_extras.py            # the 2 integration tests now run too
python -m sutra.mqtt_edge gateway --host localhost    # terminal 1: the edge gateway
python -m sutra.mqtt_edge sensors --host localhost    # terminal 2: 96 hours of two presses; watch the alerts
docker compose down -v                                # stop and delete the data
```

```powershell
docker compose up -d --wait
pip install -r requirements-extras.txt
python schema\apply.py --check
$env:SUTRA_MQTT_HOST = 'localhost'; $env:SUTRA_PG_DSN = 'postgresql://sutra:sutra@localhost:5432/sutra'; $env:SUTRA_PG_FULL = '1'
python -m pytest -q tests\test_extras.py
```

No Docker? `python -m sutra.mqtt_edge demo` runs sensors and gateway in one process, and `python schema/apply.py --without timescaledb --without vector` loads the schema into any PostgreSQL 16. QAOA needs nothing extra:

```python
from sutra.optimize import maintenance_qubo, solve_qubo
from sutra.qaoa import QiskitQAOA
Q, idx = maintenance_qubo({"press": 3.0, "oven": 1.0, "lathe": 2.0}, 2, clash=[("press", "oven")])
print(solve_qubo(Q, len(idx), QiskitQAOA(reps=2)))     # ([1, 0, 0, 1, 1, 0], -29.0, 'ibm-qiskit')
```

The **Sutra services** workflow in `.github/workflows/` runs all of this on GitHub's runners whenever Sutra changes.

**Also here**

- `schema/sutra.sql`: the production schema for PostgreSQL 16 with TimescaleDB and pgvector (reference; the proof of concept uses SQLite).
- `AGENTS.md`, `CLAUDE.md`, `.claude/` and `.codex/`: one repository set up for both Claude Code and Codex.
- `n8n/nightly-evals.json`: import into n8n with `n8n import:workflow --input=n8n/nightly-evals.json`.

Tax rates, approval limits and organisations are fictional. The QAOA adapter runs on Qiskit's simulator; to use IBM hardware, pass a `SamplerV2` and backend from `qiskit-ibm-runtime` (see the docstring in `sutra/qaoa.py`). The D-Wave and Braket adapters need their SDKs and credentials; without them the local annealer is used.
