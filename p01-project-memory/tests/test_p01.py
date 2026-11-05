import shutil
from pathlib import Path

from check import check

HERE = Path(__file__).resolve().parents[1]


def test_solution_passes():
    assert check(HERE / "solution") == []


def test_detects_long_and_unscoped(tmp_path):
    shutil.copytree(HERE / "solution", tmp_path, dirs_exist_ok=True)
    (tmp_path / "CLAUDE.md").write_text("# x\n" * 80)
    (tmp_path / ".claude/rules/api.md").write_text("# no frontmatter\n")
    problems = " ".join(check(tmp_path))
    assert "80 lines" in problems and "paths:" in problems and "Never" in problems
