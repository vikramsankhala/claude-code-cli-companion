"""Load schema/sutra.sql into PostgreSQL and check it (Chapter 32).

    python schema/apply.py --dsn postgresql://sutra:sutra@localhost:5432/sutra            # full schema
    python schema/apply.py --dsn ... --without timescaledb --without vector               # plain PostgreSQL 16
    python schema/apply.py --dsn ... --check                                              # only verify

`docker compose up db` loads the full schema on first start (TimescaleDB + pgvector image); use --check then.
The --without switches let you try the schema on a stock PostgreSQL: hypertables become ordinary tables and
vector(1024) becomes real[] (no similarity index). Everything else is identical.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

SQL = Path(__file__).with_name("sutra.sql")
EXPECTED_TABLES = 30


def adapt(sql: str, without: set[str]) -> str:
    """Remove the parts of the schema that need an extension you do not have."""
    if "timescaledb" in without:
        sql = re.sub(r"(?im)^CREATE EXTENSION IF NOT EXISTS timescaledb;\s*$", "", sql)
        sql = re.sub(r"(?im)^SELECT create_hypertable\(.*?\);\s*$", "", sql)
        sql = re.sub(r"(?ims)^SELECT add_(retention|compression)_policy\(.*?\);\s*$", "", sql)
        sql = re.sub(r"(?ims)^ALTER TABLE \w+ SET \(timescaledb\..*?\);\s*$", "", sql)
    if "vector" in without:
        sql = re.sub(r"(?im)^CREATE EXTENSION IF NOT EXISTS vector;\s*$", "", sql)
        sql = re.sub(r"(?im)^CREATE INDEX ON \w+ USING hnsw .*?;\s*$", "", sql)
        sql = re.sub(r"\bvector\(\d+\)", "real[]", sql)
    return sql


def check(conn) -> dict:
    cur = conn.cursor()
    cur.execute("SELECT extname FROM pg_extension")
    exts = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' "
                "AND table_type = 'BASE TABLE' AND table_name NOT LIKE 'event\\_p%'")
    tables = cur.fetchone()[0]
    hyper = False
    if "timescaledb" in exts:
        cur.execute("SELECT count(*) FROM timescaledb_information.hypertables WHERE hypertable_name = 'telemetry'")
        hyper = cur.fetchone()[0] == 1
    return {"tables": tables, "extensions": sorted(exts - {"plpgsql"}), "telemetry_hypertable": hyper}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Load and check the Sutra PostgreSQL schema")
    ap.add_argument("--dsn", default=os.environ.get("SUTRA_PG_DSN", "postgresql://sutra:sutra@localhost:5432/sutra"))
    ap.add_argument("--without", action="append", default=[], choices=["timescaledb", "vector"])
    ap.add_argument("--check", action="store_true", help="do not load, only verify")
    args = ap.parse_args(argv)
    import psycopg

    with psycopg.connect(args.dsn, autocommit=True) as conn:
        if not args.check:
            conn.execute(adapt(SQL.read_text(encoding="utf-8"), set(args.without)))
        info = check(conn)
    print(info)
    ok = info["tables"] >= EXPECTED_TABLES and ("timescaledb" in args.without or info["telemetry_hypertable"])
    print("schema OK" if ok else "schema INCOMPLETE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
