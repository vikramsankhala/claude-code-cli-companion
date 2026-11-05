"""Shared set-up for the NVIDIA API catalogue examples (teaching and prototyping only, not production).

Environment:
  NVIDIA_API_KEY   your personal key from build.nvidia.com (starts with nvapi-)
  NVIDIA_BASE_URL  optional; defaults to NVIDIA's hosted endpoint (tests point it at a fake server)
  NVIDIA_MODEL     optional; the chat model to use
"""
import os
import random
import sys
import time

from openai import APIStatusError, NotFoundError, OpenAI, RateLimitError

BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
CHAT_MODEL = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3.5-bolt-e4b")   # run probe_models.py to see what your key can call


def client() -> OpenAI:
    key = os.environ.get("NVIDIA_API_KEY")
    if not key:
        sys.exit("Set NVIDIA_API_KEY first (PowerShell: $env:NVIDIA_API_KEY = \"nvapi-...\").")
    return OpenAI(base_url=BASE_URL, api_key=key, max_retries=0)


def answer_text(response) -> str:
    """The visible answer. Reasoning models think first; if the token allowance runs out while
    they think, the visible answer is empty, so say so instead of printing None."""
    msg = response.choices[0].message
    if msg.content:
        return msg.content.strip()
    used = response.usage.completion_tokens if response.usage else "all"
    return (f"(no visible answer: this looks like a reasoning model that spent {used} tokens thinking; "
            "raise max_tokens or choose a model that answers directly)")


def with_backoff(call, attempts=5, base=2.0):
    """Retry on rate limits (HTTP 429) and brief server errors, waiting longer each time.
    Free tiers share roughly 40 requests a minute per account, so a class of students
    must each use their own key, and scripts must slow down instead of failing."""
    for i in range(attempts):
        try:
            return call()
        except RateLimitError:
            wait = base ** i + random.random()
        except NotFoundError:
            sys.exit("Model not found (HTTP 404): your key cannot call this model. Run probe_models.py and set NVIDIA_MODEL.")
        except APIStatusError as e:
            if e.status_code == 410:
                sys.exit("Model retired (HTTP 410 Gone). Run probe_models.py and set NVIDIA_MODEL to a current model.")
            if e.status_code in (401, 403):
                sys.exit(f"Key rejected (HTTP {e.status_code}). Check NVIDIA_API_KEY, or accept the model's terms on build.nvidia.com.")
            if e.status_code < 500:
                raise
            wait = base ** i
        if i == attempts - 1:
            raise RuntimeError("still rate-limited after retries; wait a minute or use another provider")
        print(f"  rate-limited, waiting {wait:.1f}s", file=sys.stderr)
        time.sleep(wait)
