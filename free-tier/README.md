# Free tier · NVIDIA labs and a free-model gateway

Book: Chapter 22 (22.6 is the NVIDIA section).

> **For learning and teaching only, not production.** NVIDIA's API catalogue is a free trial for prototyping, research, development, testing and evaluation; production use needs an NVIDIA AI Enterprise licence. Use synthetic or public data, never client or personal data. Read the current terms on build.nvidia.com before each course.

| Path | What it is |
| --- | --- |
| `nvidia/` | Seven lab scripts: which models your key can call (`probe_models.py`), first call, streaming, model comparison, embeddings, tool calling, a safety classifier, plus a shared helper with rate-limit back-off and clear messages for retired models |
| `litellm-config.yaml` | One local endpoint over NVIDIA, OpenRouter, Groq, Gemini and Mistral with automatic fallback |
| `scripts/test-keys.ps1` · `.sh` | Shows which of your keys work, printing status only |
| `.env.example` | The variable names; copy to `.env`, which Git ignores |
| `teaching/` | Educator guide with lesson plans, student set-up sheet, acceptable-use template |
| `tests/` | Offline tests against a fake OpenAI-compatible server (no key needed) |

## Quick start (PowerShell)

```powershell
cd free-tier
python -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt
setx NVIDIA_API_KEY "nvapi-..."          # then open a new window, reactivate, and cd back here
cd nvidia
python probe_models.py                   # which models YOUR key can call today (about 3 minutes)
$env:NVIDIA_MODEL = "nvidia/nemotron-3.5-bolt-e4b"     # or any "answers" model from the probe
python hello.py "Explain an API in two sentences"
python compare_models.py
python embed.py "How do I change my password?"
python tools.py
python guard.py "How do I pick a strong password?"
```

Model IDs change, and the catalogue lists more models than a free key can call. Run `probe_models.py` (add `--embed` for embedding models) and set `NVIDIA_MODEL`, `NVIDIA_EMBED_MODEL`, `NVIDIA_GUARD_MODEL` or `NVIDIA_COMPARE` (comma-separated) from its results.

| Message | Meaning | Fix |
| --- | --- | --- |
| `Model retired (HTTP 410 Gone)` | NVIDIA withdrew the model | Run `probe_models.py`; choose another |
| `Model not found (HTTP 404)` | Listed, but not callable with your key | Choose a model the probe marks OK |
| `(no visible answer: … reasoning model …)` | The model spent its token allowance thinking | Raise `NVIDIA_MAX_TOKENS` (try 3000; defaults are 600 for `hello.py`, 800 for `compare_models.py`) or pick an "answers" model |
| `Key rejected (HTTP 401/403)` | Key missing or wrong, or terms not accepted | Reopen the terminal after `setx`; try the model in the browser playground |
| `rate-limited, waiting…` | Over about 40 requests a minute | Nothing; the scripts wait and retry |
| Odd characters such as `â` | Windows PowerShell 5.1 display of Unicode punctuation | Use Windows Terminal or PowerShell 7 |

## The gateway

```powershell
pip install "litellm[proxy]"
litellm --config litellm-config.yaml     # http://localhost:4000, models "free-chat" and "free-embed"
```

Replace each `<model-id>` with one your accounts can call, or delete providers you have no key for.

## Tests

```powershell
python -m pytest -q        # 14 passed, offline
```
