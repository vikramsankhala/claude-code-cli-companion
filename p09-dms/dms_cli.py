"""python dms_cli.py --user priya register|version|status|get|history|search|hold|purge|audit ..."""
import argparse
import json
import os

from dms.service import DMS, load_users


def main():
    p = argparse.ArgumentParser(prog="dms")
    p.add_argument("--root", default=os.getenv("DMS_ROOT", "stores"))
    p.add_argument("--user", default=os.getenv("DMS_USER", "priya"))
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register")
    r.add_argument("file")
    for f in ("title", "type", "entity", "region", "dept", "lang"):
        r.add_argument(f"--{f}", required=True)
    r.add_argument("--class", dest="cls", default="internal")
    r.add_argument("--tags", default="")
    v = sub.add_parser("version")
    v.add_argument("doc_id"); v.add_argument("file"); v.add_argument("--note", default="")
    st = sub.add_parser("status"); st.add_argument("doc_id"); st.add_argument("new")
    g = sub.add_parser("get"); g.add_argument("doc_id"); g.add_argument("--version", type=int); g.add_argument("--to", default=".")
    sub.add_parser("history").add_argument("doc_id")
    sub.add_parser("search").add_argument("query")
    h = sub.add_parser("hold"); h.add_argument("doc_id"); h.add_argument("state", choices=["on", "off"])
    sub.add_parser("purge")
    sub.add_parser("audit").add_argument("region")
    a = p.parse_args()
    dms, user = DMS(a.root), load_users(os.getenv("DMS_USERS", "users.json"))[a.user]
    if a.cmd == "register":
        print(dms.register(user, a.file, title=a.title, doc_type=a.type, entity=a.entity, region=a.region,
                           dept=a.dept, language=a.lang, classification=a.cls,
                           tags=[t for t in a.tags.split(",") if t]))
    elif a.cmd == "version":
        print(f"v{dms.add_version(user, a.doc_id, a.file, a.note)}")
    elif a.cmd == "status":
        dms.set_status(user, a.doc_id, a.new); print("ok")
    elif a.cmd == "get":
        print(json.dumps(dms.get(user, a.doc_id, a.version, a.to), indent=2))
    elif a.cmd == "history":
        print(json.dumps(dms.history(user, a.doc_id), indent=2))
    elif a.cmd == "search":
        for d in dms.search(user, a.query):
            print(f"{d['id']}  v{d['current_version']}  {d['status']:<8} {d['language']}  {d['title']}")
            if d["snip"]:
                print(f"    {d['snip']}")
    elif a.cmd == "hold":
        dms.set_legal_hold(user, a.doc_id, a.state == "on"); print("ok")
    elif a.cmd == "purge":
        print(dms.purge_expired())
    elif a.cmd == "audit":
        for e in dms.audit_log(a.region):
            print(f"{e['ts_utc']}  {e['actor']:<8} {e['action']:<11} {e['doc_id']}  {e['detail']}")


if __name__ == "__main__":
    main()
