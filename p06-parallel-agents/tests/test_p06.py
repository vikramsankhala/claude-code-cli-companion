import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_plan import check, parse  # noqa: E402

HERE = Path(__file__).resolve().parents[1]


def test_example_plan_is_ready():
    assert check((HERE / "example/PLAN.md").read_text()) == []
    assert list(parse((HERE / "example/PLAN.md").read_text())["tasks"]) == ["bulk-discount", "receipt"]


def test_template_is_not_ready_until_filled():
    assert check((HERE / "templates/PLAN.md").read_text())


def test_shared_files_are_caught():
    text = (HERE / "example/PLAN.md").read_text().replace("shop/receipt.py", "shop/pricing.py")
    assert any("both touch shop/pricing.py" in p for p in check(text))


def test_start_tasks_dry_run():
    r = subprocess.run([sys.executable, str(HERE / "scripts/start_tasks.py"), str(HERE / "example/PLAN.md"), "--dry-run"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.count("claude -w ") == 2 and "--bg" in r.stdout
