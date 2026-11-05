"""Lab 0: which models can YOUR key call today? NVIDIA's catalogue lists more models than a free key
can use, and models are retired over time, so run this at the start of every course.
Run: python probe_models.py            chat models (about 3 minutes; it paces itself)
     python probe_models.py --embed    embedding models too
Writes working-models.txt next to this script."""
import sys
import time
from pathlib import Path

from openai import APIStatusError

from common import client

SKIP = ("guard", "safety", "reward", "clip", "parse", "detector", "translate", "deplot", "kosmos", "vila", "neva",
        "fuyu", "vision", "vlm", "cosmos", "starcoder", "llama2", "embed", "embedqa", "arctic-embed")
PAUSE = float(__import__("os").environ.get("PROBE_PAUSE", "1.6"))   # about 37 requests a minute: under the shared ~40 limit


def probe_chat(c, model):
    r = c.chat.completions.create(model=model, max_tokens=300, timeout=45,
                                  messages=[{"role": "user", "content": "Say hello in five words."}])
    text = (r.choices[0].message.content or "").strip()
    return ("answers", text[:60]) if text else ("reasoning", "thinks first; give it a larger max_tokens")


def probe_embed(c, model):
    r = c.embeddings.create(model=model, input=["hello"], encoding_format="float", timeout=45,
                            extra_body={"input_type": "query", "truncate": "END"})
    return "embeds", f"{len(r.data[0].embedding)} dimensions"


def main():
    c = client()
    ids = sorted(m.id for m in c.models.list().data)
    chat = [m for m in ids if not any(s in m for s in SKIP)]
    embed = [m for m in ids if "embed" in m] if "--embed" in sys.argv else []
    print(f"{len(ids)} models listed; testing {len(chat)} chat" + (f" and {len(embed)} embedding" if embed else "") + " models\n")
    ok = []
    for kind, models, fn in (("chat", chat, probe_chat), ("embed", embed, probe_embed)):
        for m in models:
            try:
                what, note = fn(c, m)
                print(f"OK    {m:<50} {what:<10} {note}")
                ok.append(f"{kind}\t{what}\t{m}")
            except APIStatusError as e:
                print(f"--    {m:<50} HTTP {e.status_code}")
            except Exception as e:     # timeouts and connection problems
                print(f"--    {m:<50} {type(e).__name__}")
            time.sleep(PAUSE)
    out = Path(__file__).with_name("working-models.txt")
    out.write_text("\n".join(ok) + "\n", encoding="utf-8")
    print(f"\n{len(ok)} working models saved to {out}")
    print("Use one with: $env:NVIDIA_MODEL = \"<id>\"   (PowerShell)   or   export NVIDIA_MODEL=<id>")


if __name__ == "__main__":
    main()
