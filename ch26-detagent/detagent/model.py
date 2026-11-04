"""Model adapters. Production code talks to the Protocol; tests replay a cassette byte for byte."""
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Protocol

PROMPT = """Extract these fields from the invoice text as one JSON object and nothing else:
vendor, invoice_no, currency (INR, EUR or USD), amount (number), po_number (or null).

Invoice text:
{text}"""


class Model(Protocol):
    name: str

    def complete(self, prompt: str) -> str: ...


def key(model_name: str, prompt: str) -> str:
    return hashlib.sha256(f"{model_name}\n{prompt}".encode()).hexdigest()[:16]


class Cassette:
    """Record once against a real model, then replay forever. Replay never calls the network."""

    def __init__(self, path, inner: Model | None = None, name="cassette"):
        self.path, self.inner = Path(path), inner
        self.name = inner.name if inner else name
        self.tape = json.loads(self.path.read_text()) if self.path.exists() else {}

    def complete(self, prompt: str) -> str:
        k = key(self.name, prompt)
        if k in self.tape:
            return self.tape[k]
        if self.inner is None:
            raise LookupError(f"no recording for {k}; record with a real model first")
        out = self.inner.complete(prompt)
        self.tape[k] = out
        self.path.write_text(json.dumps(self.tape, indent=2, sort_keys=True))
        return out


class OpenAICompatible:
    """Any OpenAI-compatible endpoint: Ollama, vLLM, LiteLLM, Mistral La Plateforme.
    Temperature 0 and a fixed seed reduce variation; they do not guarantee it, hence the cassette."""

    def __init__(self, model, base_url=None, api_key=None, seed=7):
        self.name = model
        self.base = (base_url or os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")).rstrip("/")
        self.key = api_key or os.environ.get("LLM_API_KEY", "ollama")
        self.seed = seed

    def complete(self, prompt: str) -> str:
        body = {"model": self.name, "temperature": 0, "seed": self.seed,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": prompt}]}
        req = urllib.request.Request(f"{self.base}/chat/completions", json.dumps(body).encode(),
                                     {"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
