import shutil
from pathlib import Path

from check import check

KIT = Path(__file__).resolve().parents[1] / "solution" / "my-kit"


def test_solution_passes():
    assert check(KIT) == []


def test_catches_unsafe_release_skill(tmp_path):
    shutil.copytree(KIT, tmp_path / "kit")
    f = tmp_path / "kit/skills/release-notes/SKILL.md"
    f.write_text(f.read_text().replace("disable-model-invocation: true\n", ""))
    assert any("disable-model-invocation" in p for p in check(tmp_path / "kit"))
