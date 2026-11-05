import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import anyio
import pytest

LABS = Path(__file__).resolve().parent.parent
APP = LABS / "practice-app"
HOOKS = LABS / "d07-guardrail" / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS))
from block_rm import check  # noqa: E402


def pytest_run(*args):
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
                          cwd=APP, capture_output=True, text=True)


def test_practice_app_tests_pass():
    r = pytest_run()
    assert r.returncode == 0, r.stdout
    assert "5 passed" in r.stdout


def test_exactly_three_planted_bugs_remain():
    r = pytest_run("exercises")
    assert "3 failed" in r.stdout, r.stdout


def test_solutions_fix_every_bug(tmp_path):
    work = tmp_path / "app"
    shutil.copytree(APP, work)
    fixes = {"shopkeeper/catalogue.py": ("start = number * size", "start = (number - 1) * size"),
             "shopkeeper/pricing.py": ("return Decimal(int((net + tax) * 100)) / 100", "return money(net + tax)"),
             "shopkeeper/inventory.py": ("if qty >= self.available(sku):", "if qty > self.available(sku):")}
    solutions = (LABS / "SOLUTIONS.md").read_text(encoding="utf-8")
    for rel, (old, new) in fixes.items():
        assert new.split("(")[0].strip() in solutions or new in solutions
        p = work / rel
        p.write_text(p.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests", "exercises"],
                       cwd=work, capture_output=True, text=True)
    assert "8 passed" in r.stdout, r.stdout


@pytest.mark.parametrize("cmd", ["rm -rf ~/tmp-test", "rm -rf /", "rm -fr $HOME/x", "rm -Rf ~",
                                 "cd x && rm -rf /etc", "rm --recursive --force ~/old", "rm -v -rf '/tmp'"])
def test_python_hook_blocks(cmd):
    assert check(cmd)


@pytest.mark.parametrize("cmd", ["ls -la", "rm -rf ./build", "rm -rf build/", "rm notes.txt", "echo rm -rf"])
def test_python_hook_allows(cmd):
    assert check(cmd) is None


def run_hook(argv, cmd):
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    return subprocess.run(argv, input=event, capture_output=True, text=True)


def test_python_hook_exit_codes():
    py = [sys.executable, str(HOOKS / "block_rm.py")]
    blocked = run_hook(py, "rm -rf ~/tmp-test")
    assert blocked.returncode == 2 and "Blocked" in blocked.stderr
    assert run_hook(py, "pytest -q").returncode == 0


@pytest.mark.skipif(os.name == "nt" or not (shutil.which("bash") and shutil.which("jq")), reason="needs bash and jq")
def test_bash_hook_matches_book():
    sh = ["bash", str(HOOKS / "block-rm.sh")]
    assert run_hook(sh, "rm -rf ~/tmp-test").returncode == 2
    assert run_hook(sh, "ls").returncode == 0


def test_settings_register_hooks():
    for name in [".claude/settings.json", "settings.bash-variant.json"]:
        s = json.loads((LABS / "d07-guardrail" / name).read_text(encoding="utf-8"))
        entry = s["hooks"]["PreToolUse"][0]
        assert entry["matcher"] == "Bash"
        script = re.search(r"hooks/([\w.-]+)", entry["hooks"][0]["command"]).group(1)
        assert (HOOKS / script).exists()


def parse(stdin, *args, cwd=None):
    return subprocess.run([sys.executable, str(LABS / "d06-pipe-and-parse" / "parse_result.py"), *args],
                          input=stdin, capture_output=True, text=True, cwd=cwd)


def test_parser_success_and_log(tmp_path):
    sample = (LABS / "d06-pipe-and-parse" / "sample-result.json").read_text(encoding="utf-8")
    log = tmp_path / "runs.csv"
    r = parse(sample, "--log", str(log))
    assert r.returncode == 0 and "Pricing fixes" in r.stdout and "$0.0187" in r.stderr
    parse(sample, "--log", str(log))
    rows = log.read_text(encoding="utf-8").strip().splitlines()
    assert rows[0].startswith("at,session_id") and len(rows) == 3


def test_parser_error_and_empty():
    err = json.dumps({"type": "result", "subtype": "error_max_turns", "is_error": True, "num_turns": 3})
    assert parse("log line\n" + err).returncode == 1
    assert parse("").returncode == 2


def test_mcp_order_tool_round_trip():
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    async def run():
        params = StdioServerParameters(command=sys.executable, args=[str(LABS / "d08-live-tool" / "orders_mcp.py")],
                                       env=dict(os.environ))
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                assert [t.name for t in (await s.list_tools()).tools] == ["order_status"]
                hit = (await s.call_tool("order_status", {"order_id": "ord-1003"})).content[0].text
                miss = (await s.call_tool("order_status", {"order_id": "ORD-9"})).content[0].text
                return hit, miss
    hit, miss = anyio.run(run)
    assert "GSTIN mismatch" in hit and "Known ids" in miss


def test_every_demo_guide_is_complete():
    for n in range(1, 9):
        guide = next(LABS.glob(f"d0{n}-*")) / "README.md"
        text = guide.read_text(encoding="utf-8")
        assert text.startswith(f"# D{n} ·") and "## Steps" in text and "## Observe" in text
        for ref in re.findall(r"\]\(([^)#:]+)\)", text):
            assert (guide.parent / ref).exists(), f"{guide}: missing {ref}"
