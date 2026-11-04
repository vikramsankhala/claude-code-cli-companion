"""Generation: answer only from retrieved sources, with numbered citations."""
import os

from .search import hybrid_search

SYSTEM = ("You answer questions for employees using ONLY the numbered sources provided. "
          "Cite every claim like [1] or [2]. If the sources do not contain the answer, reply "
          "exactly: I could not find this in the knowledge base. Never guess policy details.")


def build_prompt(question: str, hits: list[dict]) -> str:
    blocks = [f"[{i}] (source: {h['doc']})\n{h['text']}" for i, h in enumerate(hits, 1)]
    return "Sources:\n\n" + "\n\n".join(blocks) + f"\n\nQuestion: {question}"


def answer(db, embedder, question: str, depts: list[str], k: int = 5) -> dict:
    hits = hybrid_search(db, embedder, question, depts, k)
    if not hits:
        return {"answer": "I could not find this in the knowledge base.", "sources": []}
    from openai import OpenAI
    client = OpenAI(base_url=os.getenv("KB_BASE_URL", "http://localhost:11434/v1"), api_key="ollama")
    resp = client.chat.completions.create(
        model=os.getenv("KB_CHAT_MODEL", "qwen3:8b"), temperature=0,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": build_prompt(question, hits)}])
    return {"answer": resp.choices[0].message.content,
            "sources": [f"[{i}] {h['doc']}" for i, h in enumerate(hits, 1)]}
