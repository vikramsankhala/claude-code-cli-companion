"""Command line: python kb_cli.py ingest|search|ask|eval ..."""
import argparse
import json
import os

from kb import store
from kb.answer import answer
from kb.embed import get_embedder
from kb.ingest import ingest
from kb.search import hybrid_search


def allowed_depts(db) -> list[str]:
    """Access control: KB_ALLOWED_GROUPS=global,in/hr limits what this user can retrieve."""
    env = os.getenv("KB_ALLOWED_GROUPS")
    if env:
        return [d.strip() for d in env.split(",") if d.strip()]
    return [r[0] for r in db.execute("SELECT DISTINCT dept FROM chunks")]


def evaluate(db, emb, path, k=5) -> float:
    rows = [json.loads(line) for line in open(path) if line.strip()]
    hits = 0
    for r in rows:
        docs = [h["doc"] for h in hybrid_search(db, emb, r["question"], allowed_depts(db), k)]
        ok = r["expected_doc"] in docs
        hits += ok
        print(f"{'PASS' if ok else 'MISS'}  {r['question']}")
    score = hits / len(rows)
    print(f"recall@{k} = {score:.2f} ({hits}/{len(rows)})")
    return score


def main():
    p = argparse.ArgumentParser(prog="kb")
    p.add_argument("--db", default=os.getenv("KB_DB", "kb.sqlite"))
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest").add_argument("folder")
    for name in ("search", "ask"):
        sp = sub.add_parser(name)
        sp.add_argument("query")
        sp.add_argument("-k", type=int, default=5)
    sub.add_parser("eval").add_argument("golden")
    a = p.parse_args()
    db, emb = store.connect(a.db), get_embedder()
    if a.cmd == "ingest":
        print(ingest(a.folder, db, emb))
    elif a.cmd == "search":
        for i, h in enumerate(hybrid_search(db, emb, a.query, allowed_depts(db), a.k), 1):
            print(f"[{i}] {h['doc']}  score={h['score']}  via={'+'.join(h['found_by'])}")
            print("    " + h["text"].replace("\n", " ")[:160])
    elif a.cmd == "ask":
        r = answer(db, emb, a.query, allowed_depts(db), a.k)
        print(r["answer"] + "\n\nSources:\n" + "\n".join(r["sources"]))
    elif a.cmd == "eval":
        evaluate(db, emb, a.golden)


if __name__ == "__main__":
    main()
