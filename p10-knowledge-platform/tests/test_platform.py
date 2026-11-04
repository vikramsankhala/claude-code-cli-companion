"""End-to-end automation tests for the knowledge platform (offline: KB_EMBEDDER=hash)."""
import json
import os
import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import anyio
import pytest

os.environ["KB_EMBEDDER"] = "hash"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kmp.core import Platform  # noqa: E402


def make_pdf(path, lines):
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(path))
    for i, line in enumerate(lines):
        c.drawString(72, 760 - 18 * i, line)
    c.save()


def make_docx(path, paras):
    import docx
    d = docx.Document()
    for p in paras:
        d.add_paragraph(p)
    d.save(str(path))


@pytest.fixture
def kp(tmp_path):
    p = Platform(tmp_path / "data", ROOT / "users.json")
    (p.inbox / "in/hr").mkdir(parents=True)
    (p.inbox / "eu/legal").mkdir(parents=True)
    (p.inbox / "in/hr/leave.md").write_text(
        "# Leave Policy India\n\nEmployees must apply for annual leave in the HR portal. "
        "Full-time employees get 24 days of annual leave.")
    make_pdf(p.inbox / "eu/legal/wartung.pdf", ["Wartungsvertrag", "Der Vertrag ist mit einer Kuendigungsfrist "
                                                "von drei Monaten kuendbar und die Laufzeit betraegt zwei Jahre."])
    make_docx(p.inbox / "eu/legal/contrat.docx", ["Contrat de service", "Le contrat est conclu pour la durée "
                                                  "de un an et la résiliation exige un préavis de 60 jours."])
    return p


def ids_by_title(kp):
    return {d["title"]: d["id"] for d in kp.dms.search(kp.users["priya"], "status:review")} | \
           {d["title"]: d["id"] for d in kp.dms.search(kp.users["priya"], "status:approved")}


def test_inbox_to_review_is_automatic(kp):
    assert kp.scan_inbox() == 3
    kp.run()
    docs = {d["title"]: d for d in kp.dms.search(kp.users["priya"], "status:review")}
    assert docs["Wartungsvertrag"]["language"] == "de" and docs["Wartungsvertrag"]["doc_type"] == "contract"
    assert docs["Contrat de service"]["language"] == "fr"
    assert docs["Wartungsvertrag"]["classification"] == "confidential"
    assert docs["Leave Policy India"]["doc_type"] == "policy"
    notes = kp.q.db.execute("SELECT recipient, subject FROM notifications").fetchall()
    assert ("lena", f"Review needed: {docs['Wartungsvertrag']['id']}") in [tuple(n) for n in notes]
    assert kp.scan_inbox() == 0                                    # unchanged files are not re-ingested


def test_approval_publishes_and_access_is_enforced(kp):
    kp.scan_inbox(); kp.run()
    ids = ids_by_title(kp)
    priya, arjun, mike = (kp.users[n] for n in ("priya", "arjun", "mike"))
    kp.approve(priya, ids["Leave Policy India"]); kp.approve(priya, ids["Wartungsvertrag"]); kp.run()
    hits = kp.retrieve(arjun, "how many days of annual leave")
    assert hits[0]["doc"] == f"{ids['Leave Policy India']}@v1"
    assert all(not h["doc"].startswith("EU-") for h in hits)      # Arjun has no EU access
    assert kp.retrieve(mike, "annual leave") == []                 # Mike: US IT only
    de = kp.retrieve(priya, "Kuendigungsfrist Vertrag")            # German query, German document
    assert de[0]["doc"].startswith(ids["Wartungsvertrag"])


def test_update_republish_and_archive(kp):
    kp.scan_inbox(); kp.run()
    ids, priya = ids_by_title(kp), kp.users["priya"]
    doc = ids["Leave Policy India"]
    kp.approve(priya, doc); kp.run()
    (kp.inbox / "in/hr/leave.md").write_text("# Leave Policy India\n\nFull-time employees get 26 days of annual leave.")
    assert kp.scan_inbox() == 1
    kp.run()
    assert kp.retrieve(priya, "annual leave days") == []          # changed: withdrawn until re-approved
    kp.approve(priya, doc); kp.run()
    hit = kp.retrieve(priya, "annual leave days")[0]
    assert hit["doc"] == f"{doc}@v2" and "26 days" in hit["text"]
    kp.archive(priya, doc); kp.run()
    assert kp.retrieve(priya, "annual leave days") == []


def test_sql_source_incremental_sync(kp, tmp_path, monkeypatch):
    crm = tmp_path / "crm.sqlite"
    con = sqlite3.connect(crm)
    con.execute("CREATE TABLE faq (id INTEGER, question TEXT, answer TEXT, updated_at TEXT)")
    con.executemany("INSERT INTO faq VALUES (?,?,?,?)", [
        (1, "How do I reset my router?", "Hold the reset button for 10 seconds.", "2026-10-01T09:00:00Z"),
        (2, "Wie kündige ich meinen Vertrag?", "Die Kündigung ist online im Kundenportal möglich.", "2026-10-02T09:00:00Z")])
    con.commit()
    monkeypatch.setenv("CRM_DSN", str(crm))
    cfg = {"name": "crm-faq", "type": "sql", "region": "eu", "dept": "support", "driver": "sqlite3",
           "dsn_env": "CRM_DSN", "auto_approve": True, "classification": "internal",
           "query": "SELECT id, question, answer, updated_at FROM faq WHERE updated_at > ? ORDER BY updated_at",
           "columns": {"id": "id", "title": "question", "body": "answer", "updated": "updated_at"}}
    kp.sync_sources([cfg]); kp.run()
    hits = kp.retrieve(kp.users["lena"], "reset router")
    assert hits and "10 seconds" in hits[0]["text"]                # auto-approved source is live
    kp.sync_sources([cfg]); kp.run()
    assert kp.q.db.execute("SELECT COUNT(*) FROM external_items").fetchone()[0] == 2   # nothing duplicated
    con.execute("UPDATE faq SET answer='Hold the reset button for 30 seconds.', updated_at='2026-11-01T09:00:00Z' WHERE id=1")
    con.commit()
    kp.sync_sources([cfg]); kp.run()
    assert "30 seconds" in kp.retrieve(kp.users["lena"], "reset router")[0]["text"]


def test_http_source_with_pagination(kp):
    pages = {
        "/pages": {"results": [{"id": "A1", "title": "VPN troubleshooting", "body": "Error 809: router blocks the VPN port.",
                                "updated_at": "2026-10-05T10:00:00Z", "link": "https://wiki/A1"}], "next": "/pages2"},
        "/pages2": {"results": [{"id": "A2", "title": "Laptop refresh", "body": "Laptops are replaced every 4 years.",
                                 "updated_at": "2026-10-06T10:00:00Z", "link": "https://wiki/A2"}], "next": None}}

    class Wiki(BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?")[0]
            data = dict(pages[path])
            if data["next"]:
                data["next"] = f"http://127.0.0.1:{self.server.server_port}{data['next']}"
            body = json.dumps(data).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), Wiki)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    cfg = {"name": "it-wiki", "type": "http", "region": "us", "dept": "it",
           "url": f"http://127.0.0.1:{srv.server_port}/pages", "items": "results", "next": "next",
           "since_param": "updated_since",
           "fields": {"id": "id", "title": "title", "body": "body", "updated": "updated_at", "url": "link"}}
    kp.sync_sources([cfg]); kp.run()
    srv.shutdown()
    titles = {d["title"] for d in kp.dms.search(kp.users["priya"], "region:us status:review")}
    assert titles == {"VPN troubleshooting", "Laptop refresh"}     # both pages, waiting for review
    assert kp.q.db.execute("SELECT value FROM sync_state WHERE source='it-wiki'").fetchone()[0] == "2026-10-06T10:00:00Z"


def test_nightly_self_heals_reports_and_retains(kp):
    kp.scan_inbox(); kp.run()
    ids, priya = ids_by_title(kp), kp.users["priya"]
    kp.approve(priya, ids["Leave Policy India"]); kp.run()
    kp._job_unpublish(ids["Leave Policy India"])                   # simulate index drift
    assert kp.retrieve(priya, "annual leave") == []
    assert kp.retrieve(priya, "quantum teleportation budget") == []   # threshold: no false answers
    store = kp.dms.stores["eu"]
    store.db.execute("UPDATE documents SET retention_until='2000-01-01' WHERE id=?", (ids["Contrat de service"],))
    store.db.commit()
    kp.nightly(); kp.run()
    assert kp.retrieve(priya, "annual leave")                       # reconcile republished it
    assert "quantum teleportation" in (kp.root / "reports/knowledge-gaps.md").read_text()
    with pytest.raises(KeyError):
        kp.dms.get(priya, ids["Contrat de service"])               # purged by retention


def test_failed_jobs_retry_then_park(kp):
    kp.q.put("publish", doc_id="EU-999999")
    kp.run()
    row = kp.q.db.execute("SELECT status, attempts FROM jobs WHERE kind='publish'").fetchone()
    assert row["status"] == "failed" and row["attempts"] == 3


def test_mcp_server(kp):
    kp.scan_inbox(); kp.run()
    ids = ids_by_title(kp)
    kp.approve(kp.users["priya"], ids["Leave Policy India"]); kp.run()
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
    env = dict(os.environ, KMP_ROOT=str(kp.root), KMP_USER="arjun", DMS_USERS=str(ROOT / "users.json"))

    async def go():
        params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "kmp_mcp.py")], env=env)
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                names = {t.name for t in (await s.list_tools()).tools}
                assert names == {"search_documents", "retrieve_knowledge", "document_details"}
                a = (await s.call_tool("retrieve_knowledge", {"question": "annual leave"})).content[0].text
                b = (await s.call_tool("document_details", {"doc_id": ids["Leave Policy India"]})).content[0].text
                return a, b
    a, b = anyio.run(go)
    assert ids["Leave Policy India"] in a and "status: approved" in b
