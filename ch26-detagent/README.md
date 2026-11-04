# Chapter 26 · detagent: a deterministic agent

Book: Chapter 26, "Building Deterministic Agents, Step by Step".

A supplier-invoice agent whose model only extracts fields. A JSON Schema contract fences the model; a versioned policy decides; a transition table fixes the flow; model calls are recorded once and replayed; every step goes into a hash-chained journal.

```bash
pip install -r requirements.txt
python -m pytest -q                                 # 7 passed, offline
python run.py sample-invoice.txt                    # replays cassettes/invoices.json
python run.py new-invoice.txt --record devstral     # record against a real model
```

`--record` uses `LLM_BASE_URL` (default `http://localhost:11434/v1`) and `LLM_API_KEY`, so it works with Ollama, vLLM, LiteLLM or Mistral's API.
