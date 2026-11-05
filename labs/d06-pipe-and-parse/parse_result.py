"""Read `claude -p --output-format json` from stdin; print the answer and a one-line summary.
Usage: ... | python parse_result.py [--log runs.csv]   Exit code 1 if the run reported an error."""
import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path


def summarise(doc: dict) -> dict:
    return {
        "at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "session_id": doc.get("session_id", ""),
        "is_error": bool(doc.get("is_error")),
        "num_turns": doc.get("num_turns", 0),
        "duration_s": round((doc.get("duration_ms") or 0) / 1000, 1),
        "cost_usd": round(float(doc.get("total_cost_usd") or 0), 4),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", help="append a summary row to this CSV file")
    args = ap.parse_args(argv)
    raw = sys.stdin.read().strip()
    if not raw:
        print("No input. Pipe the output of: claude -p '...' --output-format json", file=sys.stderr)
        return 2
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError:           # stream-json or stray log lines: the result is the last line
        doc = json.loads(raw.splitlines()[-1])
    row = summarise(doc)
    print(doc.get("result", ""))
    print(f"\n-- {row['num_turns']} turns · {row['duration_s']} s · ${row['cost_usd']:.4f}"
          f"{' · ERROR' if row['is_error'] else ''}", file=sys.stderr)
    if args.log:
        path = Path(args.log)
        new = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)
    return 1 if row["is_error"] else 0


if __name__ == "__main__":
    sys.exit(main())
