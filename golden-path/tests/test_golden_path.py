import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

G = Path(__file__).resolve().parent.parent
ROOT = G.parent


def yml(p):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def test_every_file_parses():
    for p in list(G.rglob("*.yml")) + list(G.rglob("*.yaml")):
        assert yml(p) is not None, p
    for p in G.rglob("*.json"):
        json.loads(p.read_text(encoding="utf-8"))
    for p in G.rglob("*.toml"):
        tomllib.loads(p.read_text(encoding="utf-8"))


def revs(path):
    return {r["repo"]: r["rev"] for r in yml(path)["repos"]}


def test_hook_versions_are_pinned_and_match_the_root():
    template, root = revs(G / ".pre-commit-config.yaml"), revs(ROOT / ".pre-commit-config.yaml")
    for rev in template.values():
        assert rev.startswith("v") and rev.count(".") == 2, f"pin an exact tag, not {rev}"
    assert template == root


def test_root_lints_without_reformatting():
    hooks = [h["id"] for r in yml(ROOT / ".pre-commit-config.yaml")["repos"] for h in r["hooks"]]
    assert "ruff-check" in hooks and "gitleaks" in hooks and "ruff-format" not in hooks


def test_renovate_is_applied_unchanged():
    assert json.loads((ROOT / "renovate.json").read_text()) == json.loads((G / "renovate.json").read_text())


def test_codeowners_lines_are_well_formed():
    for p in [G / ".github" / "CODEOWNERS", ROOT / ".github" / "CODEOWNERS"]:
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                parts = line.split()
                assert any(x.startswith("@") for x in parts) and not parts[0].startswith("@"), line


def test_agent_settings_protect_secrets():
    for p in [G / ".claude" / "settings.json", ROOT / ".claude" / "settings.json"]:
        deny = json.loads(p.read_text(encoding="utf-8"))["permissions"]["deny"]
        assert any(".env" in d for d in deny)
    codex = tomllib.loads((G / ".codex" / "config.toml").read_text())
    assert codex["sandbox_workspace_write"]["network_access"] is False
    assert (ROOT / "CLAUDE.md").read_text().startswith("@AGENTS.md")
    assert "scripts/test-all.sh" in (ROOT / "AGENTS.md").read_text()


def test_ci_workflows_cover_the_golden_path():
    ci = yml(G / ".github" / "workflows" / "ci.yml")
    assert set(ci["jobs"]) == {"test", "lint", "semgrep", "secrets"}
    lint = (ROOT / ".github" / "workflows" / "lint.yml").read_text(encoding="utf-8")
    assert "pre-commit run --all-files" in lint and "golden-path/semgrep/rules.yml" in lint


@pytest.mark.skipif(not shutil.which("semgrep"), reason="semgrep not installed (CI runs it in the Lint workflow)")
def test_semgrep_rules_catch_bad_and_pass_good():
    def scan(name):
        out = subprocess.run(["semgrep", "scan", "--config", str(G / "semgrep" / "rules.yml"), "--metrics=off",
                              "--json", "--quiet", str(G / "semgrep" / "tests" / name)],
                             capture_output=True, text=True, check=False).stdout
        return sorted(r["check_id"].rsplit(".", 1)[-1] for r in json.loads(out)["results"])
    assert scan("bad_examples.py") == sorted(["hardcoded-api-key", "subprocess-shell-true",
                                              "tls-verify-disabled", "eval-of-model-output"])
    assert scan("good_examples.py") == []
