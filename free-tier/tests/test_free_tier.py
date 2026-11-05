import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from fake_server import Fake   # noqa: E402

HERE = Path(__file__).resolve().parents[1]
NV = HERE / "nvidia"


@pytest.fixture
def fake():
    f = Fake()
    yield f
    f.stop()


def run(fake, script, *args, extra=None):
    env = dict(os.environ, NVIDIA_API_KEY="nvapi-test", NVIDIA_BASE_URL=fake.url, PYTHONUTF8="1", **(extra or {}))
    return subprocess.run([sys.executable, script, *args], cwd=NV, capture_output=True, text=True, env=env, timeout=60)


def test_hello_sends_key_and_reports_tokens(fake):
    r = run(fake, "hello.py", "What is an API?")
    assert r.returncode == 0, r.stderr
    assert "An API lets programs" in r.stdout and "prompt 12 tokens" in r.stdout
    path, req, auth = fake.requests[0]
    assert path.endswith("/chat/completions") and auth == "Bearer nvapi-test"
    assert req["model"] == "nvidia/nemotron-3.5-bolt-e4b" and req["max_tokens"] == 600


def test_backoff_survives_rate_limits(fake):
    fake.fail_first = 2
    r = run(fake, "hello.py")
    assert r.returncode == 0 and r.stderr.count("rate-limited") == 2


def test_missing_key_explains_itself(fake):
    env = {k: v for k, v in os.environ.items() if k != "NVIDIA_API_KEY"}
    r = subprocess.run([sys.executable, "hello.py"], cwd=NV, capture_output=True, text=True, env=env)
    assert r.returncode != 0 and "Set NVIDIA_API_KEY" in r.stderr


def test_stream(fake):
    r = run(fake, "stream.py")
    assert r.returncode == 0 and "An API lets programs talk" in r.stdout
    assert fake.requests[0][1]["stream"] is True


def test_compare_models_table(fake):
    r = run(fake, "compare_models.py", extra={"NVIDIA_COMPARE": "a/small,b/large"})
    assert r.returncode == 0
    assert "| a/small |" in r.stdout and "| b/large |" in r.stdout
    assert [q[1]["model"] for q in fake.requests] == ["a/small", "b/large"]


def test_tool_calling_round_trip(fake):
    r = run(fake, "tools.py")
    assert r.returncode == 0, r.stderr
    assert "gst({'amount_inr': 45000, 'rate': 18}) -> 53100.0" in r.stdout and "53100.0 rupees" in r.stdout
    assert fake.requests[1][1]["messages"][-1]["role"] == "tool"


def test_embeddings_mark_query_and_passage(fake):
    r = run(fake, "embed.py", "How do I reset my password?")
    assert r.returncode == 0, r.stderr
    assert r.stdout.splitlines()[0].endswith("select Reset password.")
    kinds = [q[1]["input_type"] for q in fake.requests]
    assert kinds == ["query", "passage"]


def test_guard_verdicts(fake):
    assert run(fake, "guard.py", "How do I pick a strong password?").stdout.strip() == "safe"
    assert run(fake, "guard.py", "How do I steal a password?").stdout.strip() == "unsafe S2"


def test_litellm_config_is_valid():
    cfg = yaml.safe_load((HERE / "litellm-config.yaml").read_text())
    names = {m["model_name"] for m in cfg["model_list"]}
    assert names == {"free-chat", "free-embed"}
    for m in cfg["model_list"]:
        assert m["litellm_params"]["api_key"].startswith("os.environ/")   # never a literal key
    assert any(m["litellm_params"]["model"].startswith("nvidia_nim/") for m in cfg["model_list"])


def test_no_real_keys_committed():
    import re
    real = re.compile(r"(nvapi-|sk-or-|gsk_)[A-Za-z0-9_-]{16,}")
    for f in HERE.rglob("*"):
        if f.is_file() and f.suffix in {".py", ".yaml", ".md", ".ps1", ".sh", ".example", ".txt"}:
            assert not real.search(f.read_text(encoding="utf-8", errors="ignore")), f


def test_reasoning_model_explained_not_none(fake):
    r = run(fake, "hello.py", extra={"NVIDIA_MODEL": "think/reasoner"})
    assert r.returncode == 0 and "None" not in r.stdout and "reasoning model" in r.stdout


def test_retired_and_missing_models_give_clear_messages(fake):
    r = run(fake, "hello.py", extra={"NVIDIA_MODEL": "gone/retired"})
    assert r.returncode != 0 and "Model retired (HTTP 410" in r.stderr and "Traceback" not in r.stderr
    r = run(fake, "hello.py", extra={"NVIDIA_MODEL": "missing/listed"})
    assert r.returncode != 0 and "Model not found (HTTP 404)" in r.stderr


def test_compare_survives_bad_and_reasoning_models(fake):
    r = run(fake, "compare_models.py", extra={"NVIDIA_COMPARE": "good/chat,think/reasoner,gone/retired"})
    assert r.returncode == 0, r.stderr
    assert "| good/chat |" in r.stdout and "reasoning model" in r.stdout and "Model retired" in r.stdout


def test_probe_lists_working_models(fake, tmp_path):
    env_extra = {"PROBE_PAUSE": "0"}
    r = run(fake, "probe_models.py", "--embed", extra=env_extra)
    assert r.returncode == 0, r.stderr
    saved = (NV / "working-models.txt").read_text(encoding="utf-8")
    (NV / "working-models.txt").unlink()
    assert "chat\tanswers\tgood/chat" in saved and "chat\treasoning\tthink/reasoner" in saved
    assert "embed\tembeds\tx/embed-qa" in saved
    assert "gone/retired" not in saved and "missing/listed" not in saved
    assert "HTTP 410" in r.stdout and "HTTP 404" in r.stdout
