"""Lab 2: same prompt, several models; compare answers, speed and token use.
Run: python compare_models.py   (edit MODELS to IDs your account can call)"""
import os
import sys
import time

from common import answer_text, client, with_backoff

MODELS = os.environ.get("NVIDIA_COMPARE", "nvidia/nemotron-3.5-bolt-e4b,nvidia/nemotron-3.5-super-vl-120b-a12b").split(",")
MAX_TOKENS = int(os.environ.get("NVIDIA_MAX_TOKENS", "800"))   # reasoning models need more: try 3000
PROMPT = " ".join(sys.argv[1:]) or "A loan of 10 lakh rupees at 9% for 20 years: what is the monthly EMI? Show the formula."

c = client()
rows = []
for m in MODELS:
    print(f"asking {m} ...", file=sys.stderr, flush=True)
    t0 = time.perf_counter()
    try:
        r = with_backoff(lambda m=m: c.chat.completions.create(model=m, temperature=0, max_tokens=MAX_TOKENS, timeout=180,
                                                           messages=[{"role": "user", "content": PROMPT}]))
    except SystemExit as e:          # one unavailable model should not stop the comparison
        rows.append((m, 0.0, 0, str(e)[:90]))
        continue
    secs = time.perf_counter() - t0
    out = r.usage.completion_tokens if r.usage else 0
    rows.append((m, secs, out, answer_text(r).replace("\n", " ")[:90]))
    time.sleep(1.5)                 # stay well inside the shared rate limit

print("| Model | Seconds | Answer tokens | Start of answer |\n| --- | --- | --- | --- |")
for m, s, n, a in rows:
    print(f"| {m} | {s:.1f} | {n} | {a} |")
