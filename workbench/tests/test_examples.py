"""Smoke tests: every example that runs offline must run and print what the book quotes.
Examples that need the internet, a browser download or an API key are only compiled."""
import os
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

EX = Path(__file__).resolve().parents[1] / "examples"
NEEDS_NETWORK_OR_KEY = {"agent_list_files.py", "ask_claude.py", "count_tokens.py", "crawl_page.py",
                        "github_api.py", "parse_links.py", "screenshot_page.py", "pdf_to_markdown.py",
                        "convert_docx.py", "dashboard.py"}
SERVERS = {"app.py", "gst_server.py", "books_cli.py", "test_gst.py"}

EXPECT = {
    "pandas_basics.py": ("pandas", "South"),
    "polars_basics.py": ("polars", "West"),
    "duckdb_query.py": ("duckdb", "255"),
    "sympy_examples.py": ("sympy", "C1*sin(t) + C2*cos(t)"),
    "capm_statsmodels.py": ("statsmodels", "market"),
    "option_quantlib.py": ("QuantLib", "Call value: 11.26  Delta: 0.665"),
    "lipinski_rdkit.py": ("rdkit", "MW 180.2, logP 1.31, H-donors 1, H-acceptors 3"),
    "validate_invoice.py": ("pydantic", "45001.0"),
    "graph_deps.py": ("networkx", "Modelling"),
    "sklearn_baseline.py": ("sklearn", "Accuracy:"),
    "chart_matplotlib.py": ("matplotlib", ""),
    "chart_plotly.py": ("plotly", ""),
    "fees_xlsx.py": ("openpyxl", ""),
    "proposal_docx.py": ("docx", ""),
    "outcomes_pptx.py": ("pptx", ""),
    "pdf_basics.py": ("pymupdf", ""),
}


@pytest.fixture
def work(tmp_path):
    for f in EX.iterdir():
        if f.is_file():
            shutil.copy(f, tmp_path)
    return tmp_path


def run(work, script):
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONUTF8="1")
    return subprocess.run([sys.executable, script], cwd=work, capture_output=True, text=True, timeout=300, env=env)


@pytest.mark.parametrize("script", sorted(EXPECT))
def test_offline_example(work, script):
    module, expected = EXPECT[script]
    pytest.importorskip(module)
    if script == "pdf_basics.py":
        import pymupdf
        doc = pymupdf.open(); doc.new_page().insert_text((72, 72), "Sample book page"); doc.save(work / "book.pdf")
    r = run(work, script)
    assert r.returncode == 0, r.stderr[-800:]
    assert expected in r.stdout


def test_every_example_compiles():
    for f in EX.glob("*.py"):
        py_compile.compile(str(f), doraise=True)


def test_fastapi_app(work):
    pytest.importorskip("fastapi")
    sys.path.insert(0, str(work))
    import app
    from fastapi.testclient import TestClient
    assert TestClient(app.app).post("/ask", json={"text": "hi"}).json() == {"answer": "You asked: hi"}


def test_mcp_tool(work):
    pytest.importorskip("mcp")
    sys.path.insert(0, str(work))
    import gst_server
    assert gst_server.gst(45000) == 53100.0


def test_typer_cli(work):
    pytest.importorskip("typer")
    r = run(work, "books_cli.py")
    assert r.returncode == 0 and "Book 1" in r.stdout


def test_gst_test_file(work):
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "test_gst.py"], cwd=work, capture_output=True, text=True)
    assert "1 passed" in r.stdout


def test_listed_scripts_cover_folder():
    names = {f.name for f in EX.glob("*.py")}
    assert names == set(EXPECT) | NEEDS_NETWORK_OR_KEY | SERVERS
