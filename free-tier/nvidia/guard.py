"""Lab 5: a safety classifier as a guardrail. Llama Guard answers "safe", or "unsafe" plus category codes.
Run: python guard.py "How do I pick a strong password?" """
import os
import sys

from common import client, with_backoff

MODEL = os.environ.get("NVIDIA_GUARD_MODEL", "meta/llama-guard-4-12b")   # check the ID on its model page


def classify(c, text):
    r = with_backoff(lambda: c.chat.completions.create(model=MODEL, temperature=0, max_tokens=20,
                                                       messages=[{"role": "user", "content": text}]))
    out = (r.choices[0].message.content or "").strip()
    verdict, *codes = out.split()
    return verdict.lower(), codes


c = client()
verdict, codes = classify(c, " ".join(sys.argv[1:]) or "How do I pick a strong password?")
print(verdict, " ".join(codes))
