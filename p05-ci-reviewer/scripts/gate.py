"""Read Claude's JSON result, validate the report, print a Markdown summary and fail on high risk.
python gate.py review.json        exit 0 = pass, 1 = high risk, 2 = no valid report"""
import json
import os
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "schema" / "review.schema.json").read_text())


def load_report(path: str) -> dict | None:
    raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    report = raw.get("structured_output") if "structured_output" in raw or "result" in raw else raw
    if not report:                                     # a declined or failed run has no structured_output
        return None
    errors = list(Draft202012Validator(SCHEMA).iter_errors(report))
    return None if errors else report


def markdown(r: dict) -> str:
    lines = [f"## Claude review: risk **{r['risk']}**", "", r["summary"], ""]
    if r["findings"]:
        lines += ["| File | Line | Issue | Fix |", "| --- | --- | --- | --- |"]
        lines += [f"| `{f['file']}` | {f['line']} | {f['issue']} | {f['fix']} |" for f in r["findings"]]
    return "\n".join(lines)


def main(path: str) -> int:
    r = load_report(path)
    if r is None:
        print("No valid structured_output in the review; failing safe.", file=sys.stderr)
        return 2
    md = markdown(r)
    print(md)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(md + "\n")
    return 1 if r["risk"] == "high" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "review.json"))
