"""Lab 1b: streaming, so students see tokens arrive. Run: python stream.py"""
import sys

from common import CHAT_MODEL, client, with_backoff

c = client()
stream = with_backoff(lambda: c.chat.completions.create(
    model=CHAT_MODEL, stream=True, max_tokens=600,
    messages=[{"role": "user", "content": " ".join(sys.argv[1:]) or "Write a haiku about compilers."}]))
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
