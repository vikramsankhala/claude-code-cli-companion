"""Every template must parse, and the safety rules must be present."""
import json
import re
import tomllib
from pathlib import Path

import yaml

T = Path(__file__).resolve().parents[1]


def frontmatter(p):
    return yaml.safe_load(re.match(r"(?s)^---\n(.*?)\n---\n", p.read_text(encoding="utf-8")).group(1))


def test_json_files_parse():
    for p in list(T.rglob("*.json")):
        json.loads(p.read_text(encoding="utf-8"))


def test_toml_files_parse():
    for p in T.rglob("*.toml"):
        tomllib.loads(p.read_text(encoding="utf-8"))


def test_workflows_parse():
    for p in (T / "github").glob("*.yml"):
        wf = yaml.safe_load(p.read_text())
        assert all("timeout-minutes" in j for j in wf["jobs"].values())


def test_every_settings_file_protects_secrets():
    for p in (T / "claude" / "settings").glob("*.json"):
        s = json.loads(p.read_text())
        if "permissions" in s:
            assert "Read(./.env)" in s["permissions"]["deny"], p.name
            assert s.get("$schema"), p.name


def test_skill_and_agent_frontmatter():
    assert frontmatter(T / "claude/skills/explain-code/SKILL.md")["description"]
    a = frontmatter(T / "claude/agents/code-reviewer.md")
    assert "Edit" not in a["tools"] and a["model"] == "sonnet"


def test_scoped_rule():
    assert frontmatter(T / "claude/rules/frontend.md")["paths"]


def test_claude_md_is_short():
    assert len((T / "claude/CLAUDE.md").read_text().splitlines()) <= 60


def test_dual_agent_layout():
    d = T / "dual-agent"
    assert (d / "CLAUDE.md").read_text().splitlines()[0] == "@AGENTS.md"
    assert tomllib.loads((d / ".codex/config.toml").read_text())["sandbox_mode"] == "workspace-write"
    assert "n8n" in json.loads((d / ".mcp.json").read_text())["mcpServers"]


def test_fde_templates_complete():
    names = {p.name for p in (T / "fde").glob("*.md")}
    assert names == {"DEPLOYMENT-BRIEF.md", "EVALUATION-SHEET.md", "WEEKLY-STATUS.md", "HANDOVER-CHECKLIST.md", "FIELD-NOTE.md"}
    assert "Success measures" in (T / "fde" / "DEPLOYMENT-BRIEF.md").read_text(encoding="utf-8")
    assert "access granted to the FDE removed" in (T / "fde" / "HANDOVER-CHECKLIST.md").read_text(encoding="utf-8")
