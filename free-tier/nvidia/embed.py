"""Lab 3: embeddings for retrieval (RAG). Retrieval models are asymmetric: mark the question as a
"query" and the documents as "passage". Run: python embed.py "How do I reset my password?" """
import math
import os
import sys

from common import client, with_backoff

MODEL = os.environ.get("NVIDIA_EMBED_MODEL", "nvidia/llama-3.2-nv-embedqa-1b-v1")   # probe_models.py --embed lists working IDs
DOCS = ["To reset your password, open Settings, choose Security and select Reset password.",
        "Invoices are generated on the first working day of each month.",
        "Our office in Pune is open from 9am to 6pm, Monday to Friday."]


def embed(c, texts, kind):
    r = with_backoff(lambda: c.embeddings.create(model=MODEL, input=texts, encoding_format="float",
                                                 extra_body={"input_type": kind, "truncate": "END"}))
    return [d.embedding for d in r.data]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


c = client()
question = " ".join(sys.argv[1:]) or "How do I change my password?"
q = embed(c, [question], "query")[0]
docs = embed(c, DOCS, "passage")
for score, doc in sorted(((cosine(q, d), t) for d, t in zip(docs, DOCS)), reverse=True):
    print(f"{score:.3f}  {doc}")
