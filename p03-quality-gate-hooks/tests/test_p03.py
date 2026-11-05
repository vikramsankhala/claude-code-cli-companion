"""Feed each hook the JSON Claude Code would send, and check what it does."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
HOOKS = HERE / "solution" / ".claude" / "hooks"
APP = HERE.parent / "sample-app"


def run(hook, payload, cwd=None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(cwd or HERE))
    return subprocess.run([sys.executable, str(HOOKS / hook)], input=json.dumps(payload), text=True,
                          capture_output=True, cwd=cwd or HERE, env=env, timeout=200)


@pytest.mark.parametrize("cmd", ["rm -rf /", "rm -rf ~", "sudo rm -fr $HOME", "git push --force origin main",
                                 "git push -f", "git push origin +main"])
def test_guard_blocks(cmd):
    r = run("guard_bash.py", {"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert r.returncode == 2 and "Blocked" in r.stderr


@pytest.mark.parametrize("cmd", ["rm -rf build", "git push origin feature", "python -m pytest -q", "ls ~"])
def test_guard_allows(cmd):
    assert run("guard_bash.py", {"tool_name": "Bash", "tool_input": {"command": cmd}}).returncode == 0


@pytest.fixture
def app(tmp_path):
    dst = tmp_path / "app"
    shutil.copytree(APP, dst, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    subprocess.run(["git", "init", "-q", "-b", "feature-gst"], cwd=dst, check=True)
    return dst


def test_stop_passes_when_green(app):
    r = run("stop_tests.py", {"hook_event_name": "Stop", "stop_hook_active": False}, app)
    assert r.returncode == 0 and r.stdout.strip() == ""


def test_stop_blocks_when_red_and_never_loops(app):
    p = app / "shop" / "pricing.py"
    p.write_text(p.read_text().replace("0.18", "0.28"))
    out = json.loads(run("stop_tests.py", {"stop_hook_active": False}, app).stdout)
    assert out["decision"] == "block" and "failed" in out["reason"]
    assert run("stop_tests.py", {"stop_hook_active": True}, app).stdout.strip() == ""


def test_session_context(app):
    (app / "shop" / "cart.py").write_text((app / "shop" / "cart.py").read_text() + "\n# TODO: add bulk discounts\n")
    ctx = json.loads(run("session_context.py", {"hook_event_name": "SessionStart"}, app).stdout)
    text = ctx["hookSpecificOutput"]["additionalContext"]
    assert "feature-gst" in text and "bulk discounts" in text


@pytest.mark.skipif(not shutil.which("ruff"), reason="ruff not installed")
def test_format_hook(app):
    f = app / "shop" / "messy.py"
    f.write_text("import os\nx=1\n")
    assert run("format_file.py", {"tool_input": {"file_path": str(f)}}, app).returncode == 0
    assert f.read_text() == "x = 1\n"


def test_settings_wire_all_four_events():
    s = json.loads((HERE / "solution" / ".claude" / "settings.json").read_text())["hooks"]
    assert set(s) == {"PostToolUse", "PreToolUse", "Stop", "SessionStart"}
