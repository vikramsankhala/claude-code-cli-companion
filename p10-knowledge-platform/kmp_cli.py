"""python kmp_cli.py run|scan|nightly|approve|archive|search|ask|status [...]"""
import argparse
import json
import os

from kmp.core import Platform


def main():
    p = argparse.ArgumentParser(prog="kmp")
    p.add_argument("--root", default=os.getenv("KMP_ROOT", "data"))
    p.add_argument("--user", default=os.getenv("KMP_USER", "priya"))
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run", help="scan the inbox and process every pending job")
    sub.add_parser("nightly", help="queue reconcile, retention and gap-report jobs, then run them")
    sub.add_parser("sync", help="pull changes from every source in sources.json, then run the jobs")
    for name in ("approve", "archive"):
        sub.add_parser(name).add_argument("doc_id")
    sub.add_parser("search").add_argument("query")
    sub.add_parser("ask").add_argument("question")
    sub.add_parser("status", help="queue and notification summary")
    a = p.parse_args()
    kp = Platform(a.root)
    user = kp.users[a.user]
    if a.cmd == "run":
        print(f"queued {kp.scan_inbox()} new files, ran {kp.run()} jobs")
    elif a.cmd == "nightly":
        kp.nightly()
        print(f"ran {kp.run()} jobs")
    elif a.cmd == "sync":
        kp.sync_sources(kp.load_sources(os.getenv("KMP_SOURCES", "sources.json")))
        print(f"ran {kp.run()} jobs")
    elif a.cmd == "approve":
        kp.approve(user, a.doc_id); print(f"ran {kp.run()} jobs")
    elif a.cmd == "archive":
        kp.archive(user, a.doc_id); print(f"ran {kp.run()} jobs")
    elif a.cmd == "search":
        for d in kp.dms.search(user, a.query):
            print(f"{d['id']}  {d['status']:<8} {d['language']}  {d['title']}")
    elif a.cmd == "ask":
        r = kp.ask(user, a.question)
        print(r["answer"] + "\n\nSources:\n" + "\n".join(r["sources"]))
    elif a.cmd == "status":
        jobs = kp.q.db.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status").fetchall()
        print(json.dumps({"jobs": dict(jobs),
                          "notifications": kp.q.db.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]}))


if __name__ == "__main__":
    main()
