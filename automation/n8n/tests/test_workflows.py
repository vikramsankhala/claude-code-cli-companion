import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent
FILES = sorted((ROOT / "workflows").glob("*.json")) + [REPO / "part11-sutra-erp" / "n8n" / "nightly-evals.json"]
SECRET = re.compile(r"(nvapi-|sk-[A-Za-z0-9]{10}|ghp_|xox[bp]-|AKIA[0-9A-Z]{12}|Bearer\s+[A-Za-z0-9._-]{16})")


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def is_trigger(n):
    return n["type"].lower().endswith("trigger")


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_structure(path):
    wf = load(path)
    names = [n["name"] for n in wf["nodes"]]
    assert wf["name"] and len(names) == len(set(names)), "node names must be unique"
    for n in wf["nodes"]:
        assert {"parameters", "name", "type", "typeVersion", "position"} <= n.keys(), n["name"]
        assert len(n["position"]) == 2
    assert sum(is_trigger(n) for n in wf["nodes"]) == 1, "exactly one trigger"
    for src, outs in wf["connections"].items():
        assert src in names, f"connection from unknown node {src}"
        for kind, branches in outs.items():
            for branch in branches:
                for c in branch:
                    assert c["node"] in names, f"{src} -> unknown {c['node']}"
                    assert c["type"] == kind


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_node_reachable_from_trigger(path):
    wf = load(path)
    edges = {}
    for src, outs in wf["connections"].items():
        for branches in outs.values():
            for branch in branches:
                for c in branch:      # sub-nodes (models, tools) point at their parent: treat links as undirected
                    edges.setdefault(src, set()).add(c["node"])
                    edges.setdefault(c["node"], set()).add(src)
    start = next(n["name"] for n in wf["nodes"] if is_trigger(n))
    seen, todo = {start}, [start]
    while todo:
        for nxt in edges.get(todo.pop(), ()):
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    assert seen == {n["name"] for n in wf["nodes"]}


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_agent_commands_have_guardrails(path):
    for n in load(path)["nodes"]:
        if n["type"] != "n8n-nodes-base.executeCommand":
            continue
        cmd = n["parameters"]["command"]
        if "claude -p" in cmd:
            assert "--max-turns" in cmd and ("--permission-mode plan" in cmd or "acceptEdits" in cmd), n["name"]
        if "codex exec" in cmd:
            assert "--sandbox read-only" in cmd, n["name"]
        assert "$json.body" not in cmd, "untrusted webhook text must never reach a shell"


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_credentials_or_keys(path):
    wf = load(path)
    assert all("credentials" not in n for n in wf["nodes"]), "export without credentials"
    assert not SECRET.search(path.read_text(encoding="utf-8"))


def test_readme_lists_every_workflow():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for p in (ROOT / "workflows").glob("*.json"):
        assert f"workflows/{p.name}" in readme


def test_mcp_tools_are_attached_to_the_trigger():
    wf = load(ROOT / "workflows" / "04-mcp-agent-tools.json")
    tools = [n["name"] for n in wf["nodes"] if n["type"].startswith("@n8n/n8n-nodes-langchain.tool")]
    assert sorted(tools) == ["create_ticket", "order_status"]
    for t in tools:
        assert wf["connections"][t]["ai_tool"][0][0]["node"] == "MCP Server Trigger"


@pytest.mark.skipif(not __import__("shutil").which("node"), reason="needs Node.js")
def test_javascript_snippets_behave(tmp_path):
    import subprocess
    script = tmp_path / "check.js"
    script.write_text("""
const wf4 = require(process.argv[2]), wf1 = require(process.argv[3]);
const ticket = new Function('query', wf4.nodes.find(n => n.name === 'create_ticket').parameters.jsCode);
const parse = new Function('$json', wf1.nodes.find(n => n.name === 'Parse result').parameters.jsCode);
const out = {
  ok: JSON.parse(ticket(JSON.stringify({ title: 'Order on hold: GSTIN', priority: 'urgent' }))).priority,
  short: ticket({ title: 'x' }), secret: ticket({ title: 'Reset my account', details: 'api_key=1' }),
  good: parse({ stdout: JSON.stringify({ result: 'fine', num_turns: 2, is_error: false }), exitCode: 0 }).json.ok,
  bad: parse({ stdout: 'not json', exitCode: 0 }).json.ok,
};
console.log(JSON.stringify(out));""", encoding="utf-8")
    wf = ROOT / "workflows"
    r = subprocess.run(["node", str(script), str(wf / "04-mcp-agent-tools.json"), str(wf / "01-ci-failure-summary.json")],
                       capture_output=True, text=True, check=True)
    out = json.loads(r.stdout)
    assert out["ok"] == "medium" and out["short"].startswith("Refused") and out["secret"].startswith("Refused")
    assert out["good"] is True and out["bad"] is False
