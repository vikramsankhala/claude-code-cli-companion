"""Sutra extras: the Qiskit QAOA adapter, the MQTT edge simulator and the PostgreSQL schema.
Integration tests run only when a service is there:
  SUTRA_MQTT_HOST=localhost (and SUTRA_MQTT_PORT)       real broker round trip
  SUTRA_PG_DSN=postgresql://sutra:sutra@localhost:5432/sutra   schema checks; SUTRA_PG_FULL=1 also needs TimescaleDB
`docker compose up -d --wait` starts both."""
import itertools
import json
import os
import sys
import time
from pathlib import Path

import pytest
import yaml

from sutra.iot import EdgeMonitor
from sutra.mqtt_edge import EdgeGateway, MemoryBroker, main, run_sensors, summarise, topic_matches
from sutra.optimize import brute_force, energy, maintenance_qubo, solve_qubo
from sutra.qaoa import ising_energy, qubo_to_ising

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "schema"))
from apply import adapt, check  # noqa: E402

JOBS = {"press": 3.0, "oven": 1.0, "lathe": 2.0}


def test_ising_mapping_is_exact_for_every_bitstring():
    Q, idx = maintenance_qubo(JOBS, 2, clash=[("press", "oven")])
    n = len(idx)
    h, J, c = qubo_to_ising(Q, n)
    for x in itertools.product((0, 1), repeat=n):
        assert ising_energy(h, J, c, [1 - 2 * b for b in x]) == pytest.approx(energy(Q, list(x)))


def test_qaoa_finds_the_brute_force_optimum():
    from sutra.optimize import QiskitQAOA  # lazy re-export from sutra.qaoa
    Q, idx = maintenance_qubo(JOBS, 2, clash=[("press", "oven")])
    provider = QiskitQAOA(reps=2, seed=7)
    x, e, solver = solve_qubo(Q, len(idx), provider)
    bx, be = brute_force(Q, len(idx))
    assert solver == "ibm-qiskit" and e == pytest.approx(be)
    plan = {j: s for (j, s), i in idx.items() if x[i]}
    assert sorted(plan) == sorted(JOBS) and plan["press"] != plan["oven"]
    assert provider.report["qubits"] == 6 and 0 < provider.report["best_probability"] <= 1


def test_qaoa_refuses_too_many_qubits_and_falls_back():
    from sutra.qaoa import QiskitQAOA
    jobs = {f"m{i}": 1.0 for i in range(8)}
    Q, idx = maintenance_qubo(jobs, 3, clash=[])
    x, e, solver = solve_qubo(Q, len(idx), QiskitQAOA(max_qubits=20))   # 24 qubits: the adapter refuses
    assert solver == "local-anneal"


@pytest.mark.parametrize("pattern,topic,ok", [
    ("sutra/+/+/+", "sutra/pune/press-01/current_a", True),
    ("sutra/+/+/+", "sutra/pune/press-01", False),
    ("sutra/#", "sutra/pune/press-01/alerts", True),
    ("sutra/pune/+/alerts", "sutra/delhi/press-01/alerts", False),
    ("sutra/+/press-01/#", "sutra/pune/press-01/x/y", True),
])
def test_topic_matching(pattern, topic, ok):
    assert topic_matches(pattern, topic) is ok


def test_gateway_predicts_before_the_threshold():
    bus = MemoryBroker()
    gw = EdgeGateway(bus)
    upstream = []
    bus.subscribe("sutra/+/+/alerts", lambda t, p: upstream.append(json.loads(p)))
    sent = run_sensors(bus, "pune", hours=96)
    assert sent == 96 * 2 * 3 and gw.stats["readings"] == sent
    first = summarise(gw.alerts)
    assert first["press-01 vibration_mm_s predictive/warning"] < first["press-01 vibration_mm_s threshold/warning"]
    assert "press-02 current_a threshold/warning" in first                 # the injected current spike
    assert len(upstream) == len(gw.alerts) and all(a["site"] == "pune" for a in upstream)
    assert len(upstream) < sent / 20                                       # only alerts leave the site


def test_gateway_survives_bad_payloads_and_skips_bad_quality():
    bus = MemoryBroker()
    gw = EdgeGateway(bus, monitor=EdgeMonitor())
    bus.publish("sutra/pune/press-01/current_a", b"not json")
    bus.publish("sutra/pune/press-01/current_a", json.dumps({"t": 1}).encode())
    bus.publish("sutra/pune/press-01/current_a", json.dumps({"t": 1, "v": 60, "q": 0}).encode())
    bus.publish("sutra/pune/press-01/current_a", json.dumps({"t": 2, "v": 60}).encode())
    assert gw.stats == {"bad_payload": 2, "bad_quality": 1, "readings": 1}
    assert gw.alerts[0]["severity"] == "critical"


def test_demo_command(capsys):
    assert main(["demo", "--hours", "96"]) == 0
    assert "alerts published upstream" in capsys.readouterr().out


def test_adapt_strips_only_extension_features():
    sql = (ROOT / "schema" / "sutra.sql").read_text(encoding="utf-8")
    plain = adapt(sql, {"timescaledb", "vector"})
    for gone in ["timescaledb", "create_hypertable", "vector(", "hnsw"]:
        assert gone not in plain
    assert plain.count("CREATE TABLE") == sql.count("CREATE TABLE")
    assert adapt(sql, set()) == sql


def test_compose_file_matches_the_code():
    c = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    db, mq = c["services"]["db"], c["services"]["mqtt"]
    assert "timescaledb-ha:pg16" in db["image"] and "eclipse-mosquitto:2" in mq["image"]
    assert any("schema/sutra.sql:/docker-entrypoint-initdb.d/" in v for v in db["volumes"])
    for svc in (db, mq):
        assert "healthcheck" in svc and all(p.startswith("127.0.0.1:") for p in svc["ports"])
    for v in mq["volumes"] + db["volumes"]:
        src = v.split(":")[0]
        assert not src.startswith("./") or (ROOT / src).exists(), src


# --- Integration: run with `docker compose up -d --wait` ------------------------------------------------------
MQTT = os.environ.get("SUTRA_MQTT_HOST")
PG = os.environ.get("SUTRA_PG_DSN")


@pytest.mark.skipif(not MQTT, reason="set SUTRA_MQTT_HOST to test against a real broker")
def test_real_broker_round_trip():
    from sutra.mqtt_edge import PahoTransport
    port = int(os.environ.get("SUTRA_MQTT_PORT", "1883"))
    gw_bus = PahoTransport(MQTT, port, client_id="test-gateway")
    sensors = PahoTransport(MQTT, port, client_id="test-sensors")
    try:
        gw = EdgeGateway(gw_bus, site="ci")
        sent = run_sensors(sensors, "ci", hours=96)
        sensors.flush()
        deadline = time.monotonic() + 30
        while gw.stats["readings"] < sent and time.monotonic() < deadline:
            time.sleep(0.1)
        assert gw.stats["readings"] == sent
        ref = EdgeGateway(MemoryBroker(), site="ci")
        run_sensors(ref.bus, "ci", hours=96)
        assert summarise(gw.alerts) == summarise(ref.alerts)    # same alerts over the network as in memory
    finally:
        gw_bus.close()
        sensors.close()


@pytest.mark.skipif(not PG, reason="set SUTRA_PG_DSN to test the schema in PostgreSQL")
def test_schema_in_postgres():
    psycopg = pytest.importorskip("psycopg")
    with psycopg.connect(PG, autocommit=True) as conn:
        info = check(conn)
        assert info["tables"] >= 30 and "pgcrypto" in info["extensions"]
        if os.environ.get("SUTRA_PG_FULL") == "1":
            assert info["telemetry_hypertable"] and {"timescaledb", "vector"} <= set(info["extensions"])
        with conn.transaction(force_rollback=True):
            t = conn.execute("INSERT INTO tenant (name, home_region) VALUES ('Test', 'in') RETURNING id").fetchone()[0]
            with pytest.raises(psycopg.errors.CheckViolation):
                with conn.transaction():
                    conn.execute("INSERT INTO tenant (name, home_region) VALUES ('Bad', 'mars')")
            if "vector" in info["extensions"]:
                v = "[" + ",".join(["0.1"] * 1024) + "]"
                conn.execute("INSERT INTO kb_chunk (tenant_id, access_group, text, embedding) VALUES (%s, 'all', 'hi', %s)",
                             (t, v))
                assert conn.execute("SELECT text FROM kb_chunk ORDER BY embedding <=> %s LIMIT 1", (v,)).fetchone()[0] == "hi"
