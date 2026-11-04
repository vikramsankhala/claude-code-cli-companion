"""Hybrid retrieval: keyword and vector results fused with Reciprocal Rank Fusion."""
from . import store


def rrf(ranked_lists: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    """score(d) = sum over lists of 1 / (k + rank). Rewards items ranked well by either list."""
    scores: dict[int, float] = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: -kv[1])


def hybrid_search(db, embedder, query: str, depts: list[str], k: int = 5, pool: int = 20) -> list[dict]:
    kw = store.keyword_search(db, query, depts, pool)
    vec = store.vector_search(db, embedder.embed([query])[0], depts, pool)
    fused = rrf([kw, vec])[:k]
    rows = store.get_chunks(db, [i for i, _ in fused])
    hits = []
    for cid, score in fused:
        h = rows[cid]
        h["score"] = round(score, 4)
        h["found_by"] = [n for n, lst in (("keyword", kw), ("vector", vec)) if cid in lst]
        hits.append(h)
    return hits
