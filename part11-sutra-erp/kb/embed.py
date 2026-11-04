"""Embeddings: turn text into vectors so similar meanings sit close together."""
import hashlib
import os
import re

import numpy as np

DIM = 384


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class HashEmbedder:
    """Offline, deterministic stand-in for a real embedding model.
    Used for tests and for learning; it matches shared words and word pairs only."""
    name = "hash-384"

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), DIM), dtype=np.float32)
        for i, t in enumerate(texts):
            toks = tokens(t)
            for a, b in zip(toks, toks[1:] + [""]):
                for feat in (a, f"{a}_{b}"):
                    h = int(hashlib.md5(feat.encode()).hexdigest(), 16)
                    out[i, h % DIM] += 1.0 if (h >> 8) & 1 else -1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return out / norms


class OllamaEmbedder:
    """Real semantic embeddings from a local model served by Ollama."""

    def __init__(self):
        from openai import OpenAI
        self.name = os.getenv("KB_EMBED_MODEL", "bge-m3")  # multilingual
        self.client = OpenAI(base_url=os.getenv("KB_BASE_URL", "http://localhost:11434/v1"),
                             api_key="ollama")

    def embed(self, texts: list[str]) -> np.ndarray:
        resp = self.client.embeddings.create(model=self.name, input=texts)
        vecs = np.array([d.embedding for d in resp.data], dtype=np.float32)
        return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)


def get_embedder():
    return HashEmbedder() if os.getenv("KB_EMBEDDER") == "hash" else OllamaEmbedder()
