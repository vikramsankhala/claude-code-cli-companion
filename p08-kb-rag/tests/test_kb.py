"""Offline tests: no model download needed (KB_EMBEDDER=hash)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import anyio
import pytest

os.environ["KB_EMBEDDER"] = "hash"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kb import store                      # noqa: E402
from kb.embed import HashEmbedder         # noqa: E402
from kb.ingest import chunk_markdown, ingest  # noqa: E402
from kb.search import hybrid_search, rrf  # noqa: E402
from kb.answer import build_prompt        # noqa: E402

EMB = HashEmbedder()


@pytest.fixture
def kb(tmp_path):
    docs = tmp_path / "docs"
    shutil.copytree(ROOT / "docs", docs)
    db = store.connect(str(tmp_path / "kb.sqlite"))
    ingest(str(docs), db, EMB)
    return db, docs


def test_chunks_carry_title_and_section():
    chunks = chunk_markdown("# Guide\n\n## Setup\n\nInstall it.", "Guide")
    assert chunks == ["Guide > Setup\n\nInstall it."]


def test_rrf_rewards_agreement():
    fused = dict(rrf([[1, 2, 3], [3, 1, 4]]))
    assert fused[1] > fused[2] and fused[3] > fused[4]


def test_hybrid_finds_exact_terms(kb):
    db, _ = kb
    hits = hybrid_search(db, EMB, "error 809", ["global", "in", "de"], k=3)
    assert hits[0]["doc"] == "global/it/vpn-setup.md"
    assert "keyword" in hits[0]["found_by"]


def test_accents_are_ignored(kb):
    db, _ = kb
    hits = hybrid_search(db, EMB, "arztliche Arbeitsunfahigkeitsbescheinigung", ["de"], k=1)
    assert hits[0]["doc"] == "de/hr/urlaubsrichtlinie.md"


def test_access_groups_filter_results(kb):
    db, _ = kb
    docs = {h["doc"] for h in hybrid_search(db, EMB, "Urlaubstage leave days", ["global", "in"], k=10)}
    assert "de/hr/urlaubsrichtlinie.md" not in docs
    assert "in/hr/leave-policy.md" in docs


def test_incremental_ingest(kb):
    db, docs = kb
    assert ingest(str(docs), db, EMB)["skipped"] == 7
    (docs / "global/it/vpn-setup.md").write_text("# VPN Setup Guide\n\n## New\n\nUse client version 9.")
    (docs / "global/finance/travel-approval.md").unlink()
    stats = ingest(str(docs), db, EMB)
    assert stats["updated"] == 1 and stats["removed"] == 1
    assert not hybrid_search(db, EMB, "error 809", ["global"], k=5) or \
        all("809" not in h["text"] for h in hybrid_search(db, EMB, "error 809", ["global"], k=5))


def test_prompt_numbers_sources():
    p = build_prompt("Q?", [{"doc": "a.md", "text": "A"}, {"doc": "b.md", "text": "B"}])
    assert "[1] (source: a.md)" in p and "[2] (source: b.md)" in p


def test_golden_recall(tmp_path):
    db_path = tmp_path / "kb.sqlite"
    env = dict(os.environ, KB_EMBEDDER="hash")
    subprocess.run([sys.executable, "kb_cli.py", "--db", str(db_path), "ingest", "docs"],
                   cwd=ROOT, env=env, check=True, capture_output=True)
    out = subprocess.run([sys.executable, "kb_cli.py", "--db", str(db_path), "eval", "eval/golden.jsonl"],
                         cwd=ROOT, env=env, check=True, capture_output=True, text=True).stdout
    assert "recall@5 = 1.00" in out


def test_mcp_server_round_trip(tmp_path):
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    db_path = tmp_path / "kb.sqlite"
    env = dict(os.environ, KB_EMBEDDER="hash", KB_DB=str(db_path), KB_ALLOWED_GROUPS="global")
    subprocess.run([sys.executable, "kb_cli.py", "--db", str(db_path), "ingest", "docs"],
                   cwd=ROOT, env=env, check=True, capture_output=True)

    async def run():
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "kb_mcp.py")], env=env)
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                tools = [t.name for t in (await s.list_tools()).tools]
                assert "search_knowledge" in tools
                res = await s.call_tool("search_knowledge", {"query": "password length"})
                return res.content[0].text
    text = anyio.run(run)
    assert "global/it/password-policy.md" in text
    assert "de/hr" not in text
