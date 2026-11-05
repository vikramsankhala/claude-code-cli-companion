"""Lab 1: the first call. Run: python hello.py "Explain an API in two sentences" """
import os
import sys

from common import CHAT_MODEL, answer_text, client, with_backoff

prompt = " ".join(sys.argv[1:]) or "In two sentences, what is an API?"
c = client()
r = with_backoff(lambda: c.chat.completions.create(
    model=CHAT_MODEL, temperature=0.2, max_tokens=int(os.environ.get("NVIDIA_MAX_TOKENS", "600")),
    messages=[{"role": "user", "content": prompt}]))
print(answer_text(r))
u = r.usage
if u:
    print(f"\n[{CHAT_MODEL}] prompt {u.prompt_tokens} tokens, answer {u.completion_tokens} tokens")
