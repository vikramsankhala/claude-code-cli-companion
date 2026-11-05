import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parents[1]
GATE = HERE / "scripts" / "gate.py"


def gate(sample):
    return subprocess.run([sys.executable, str(GATE), str(HERE / "samples" / sample)], capture_output=True, text=True)


def test_schema_is_valid():
    Draft202012Validator.check_schema(json.loads((HERE / "schema/review.schema.json").read_text()))


def test_high_risk_fails_the_job():
    r = gate("review-high.json")
    assert r.returncode == 1 and "risk **high**" in r.stdout and "shop/pricing.py" in r.stdout


def test_low_risk_passes():
    assert gate("review-low.json").returncode == 0


def test_missing_output_fails_safe():
    r = gate("review-declined.json")
    assert r.returncode == 2 and "failing safe" in r.stderr


def test_workflows_are_valid_yaml():
    import yaml
    for f in (HERE / "ci-examples").glob("*.yml"):
        wf = yaml.safe_load(f.read_text())
        assert "jobs" in wf and wf["jobs"]["review"]["timeout-minutes"] <= 15
