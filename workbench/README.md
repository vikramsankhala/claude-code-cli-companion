# Workbench · Python and the terminal (Part XII)

Book: Part XII, Chapters 37 to 43.

| Folder | What it holds | Book |
| --- | --- | --- |
| `examples/` | Every package example from Chapters 38 and 39 as a runnable script, plus `sales.csv` | Chapters 38, 39 |
| `practice/` | Starter and reference files for the six weeks of daily practice | Chapter 43 |
| `tests/` | Runs every offline example and checks the outputs the book quotes | |

## Set up the work environment (Chapter 39)

```powershell
cd workbench
uv venv --python 3.13 --seed
.venv\Scripts\activate              # macOS, Linux: source .venv/bin/activate
uv pip install -r requirements.txt
```

`requirements.txt` is the full Chapter 39 environment. `requirements-ci.txt` is a lighter set, without browsers or notebooks, that is enough for the tests.

## Run the examples

```powershell
cd examples
python pandas_basics.py             # offline examples print straight away
python option_quantlib.py           # Call value: 11.26  Delta: 0.665
uvicorn app:app --reload            # then open http://127.0.0.1:8000/docs
streamlit run dashboard.py
claude mcp add gst -- python gst_server.py
```

| Needs | Examples |
| --- | --- |
| Nothing (offline) | `pandas_basics`, `polars_basics`, `duckdb_query`, `chart_matplotlib`, `chart_plotly`, `sklearn_baseline`, `fees_xlsx`, `proposal_docx`, `outcomes_pptx`, `sympy_examples`, `capm_statsmodels`, `option_quantlib`, `lipinski_rdkit`, `validate_invoice`, `graph_deps`, `books_cli`, `pdf_basics` |
| The internet | `github_api`, `parse_links`, `count_tokens` (first run downloads the tokeniser) |
| A browser download (`python -m playwright install chromium`) | `screenshot_page`, `crawl_page` |
| `ANTHROPIC_API_KEY` or a Claude Code sign-in | `ask_claude`, `agent_list_files` |
| Your own files | `pdf_to_markdown` (`report.pdf`), `convert_docx` (`proposal.docx`), `dashboard` (upload a CSV) |

## Test

```powershell
python -m pytest -q tests practice/fintech
```
