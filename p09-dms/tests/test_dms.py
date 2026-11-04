"""End-to-end tests for the multinational DMS. Run: python -m pytest -q"""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dms.service import DMS, AccessDenied, load_users  # noqa: E402

USERS = load_users(ROOT / "users.json")
PRIYA, ARJUN, LENA, MIKE = (USERS[n] for n in ("priya", "arjun", "lena", "mike"))


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
def env(tmp_path):
    files = tmp_path / "in"
    files.mkdir()
    (files / "vpn.md").write_text("# VPN standard\n\nAll staff must use the corporate VPN with MFA.")
    make_pdf(files / "vertrag.pdf", ["Rahmenvertrag Wartung", "Kuendigungsfrist drei Monate zum Quartalsende."])
    make_docx(files / "contrat.docx", ["Contrat de service", "Clause de résiliation : préavis de 60 jours."])
    dms = DMS(tmp_path / "stores")
    ids = {
        "vpn": dms.register(PRIYA, files / "vpn.md", title="VPN standard", doc_type="policy", entity="Acme Inc",
                            region="us", dept="it", language="en", tags=["security"]),
        "de": dms.register(PRIYA, files / "vertrag.pdf", title="Rahmenvertrag Wartung", doc_type="contract",
                           entity="Acme GmbH", region="eu", dept="legal", language="de", classification="confidential"),
        "fr": dms.register(PRIYA, files / "contrat.docx", title="Contrat de service", doc_type="contract",
                           entity="Acme SAS", region="eu", dept="legal", language="fr"),
    }
    return dms, ids, files, tmp_path


def test_ids_and_residency(env):
    dms, ids, _, tmp = env
    assert ids["vpn"].startswith("US-") and ids["de"].startswith("EU-")
    assert (tmp / "stores/eu/dms.sqlite").exists() and (tmp / "stores/us/dms.sqlite").exists()
    assert dms.get(PRIYA, ids["de"])["path"].startswith(str(tmp / "stores/eu"))


def test_full_text_across_formats_and_languages(env):
    dms, ids, _, _ = env
    assert [d["id"] for d in dms.search(PRIYA, "MFA")] == [ids["vpn"]]
    assert [d["id"] for d in dms.search(PRIYA, "Kuendigungsfrist")] == [ids["de"]]   # PDF
    assert [d["id"] for d in dms.search(PRIYA, "resiliation")] == [ids["fr"]]        # DOCX, accent-free query
    assert "[" in dms.search(PRIYA, "MFA")[0]["snip"]                                  # highlighted snippet


def test_filters(env):
    dms, ids, _, _ = env
    assert {d["id"] for d in dms.search(PRIYA, "type:contract")} == {ids["de"], ids["fr"]}
    assert [d["id"] for d in dms.search(PRIYA, "type:contract lang:fr")] == [ids["fr"]]
    assert [d["id"] for d in dms.search(PRIYA, "tag:security status:draft")] == [ids["vpn"]]
    assert dms.search(PRIYA, 'entity:"Acme GmbH"')[0]["id"] == ids["de"]


def test_access_control_and_audit(env):
    dms, ids, _, _ = env
    assert dms.search(MIKE, "type:contract") == []                 # wrong region
    assert {d["id"] for d in dms.search(LENA, "type:contract")} == {ids["de"], ids["fr"]}
    with pytest.raises(AccessDenied):
        dms.get(MIKE, ids["de"])
    assert any(e["action"] == "denied" and e["actor"] == "mike" for e in dms.audit_log("eu"))


def test_workflow_and_versions(env):
    dms, ids, files, _ = env
    doc = ids["vpn"]
    with pytest.raises(ValueError):
        dms.set_status(PRIYA, doc, "approved")                       # must go through review
    dms.set_status(PRIYA, doc, "review")
    with pytest.raises(AccessDenied):
        dms.set_status(MIKE, doc, "approved")                        # Mike cannot approve
    dms.set_status(PRIYA, doc, "approved")
    v1 = dms.get(PRIYA, doc)["sha256"]
    (files / "vpn2.md").write_text("# VPN standard\n\nUse VPN client 9 with hardware keys.")
    assert dms.add_version(PRIYA, doc, files / "vpn2.md", "client 9") == 2
    d = dms.get(PRIYA, doc)
    assert d["status"] == "draft" and d["version"] == 2              # changed content needs re-approval
    assert dms.get(PRIYA, doc, version=1)["sha256"] == v1
    assert dms.search(PRIYA, "MFA") == []                            # index holds the current version
    assert len(dms.history(PRIYA, doc)) == 2


def test_retention_and_legal_hold(env):
    dms, ids, _, _ = env
    dms.set_legal_hold(PRIYA, ids["de"], True)
    blob = Path(dms.get(PRIYA, ids["fr"])["path"])
    purged = dms.purge_expired(today="2100-01-01")
    assert ids["fr"] in purged and ids["de"] not in purged and not blob.exists()


def test_rest_api(env, monkeypatch):
    _, _, files, tmp = env
    monkeypatch.setenv("DMS_ROOT", str(tmp / "stores"))
    monkeypatch.setenv("DMS_USERS", str(ROOT / "users.json"))
    sys.modules.pop("api", None)
    from fastapi.testclient import TestClient
    import api
    c = TestClient(api.app)
    with open(files / "vpn.md", "rb") as fh:
        r = c.post("/documents", headers={"X-User": "arjun"},
                   data={"title": "Payroll calendar", "doc_type": "policy", "entity": "Acme India Pvt Ltd",
                         "region": "in", "dept": "finance", "language": "en"},
                   files={"file": ("payroll.md", fh, "text/markdown")})
    assert r.status_code == 201 and r.json()["id"].startswith("IN-")
    assert c.get("/search", params={"q": "MFA"}, headers={"X-User": "arjun"}).json()[0]["region"] == "in"
    assert c.get("/documents/EU-000001", headers={"X-User": "arjun"}).status_code == 403
    body = c.get(f"/documents/{r.json()['id']}/versions/1/content", headers={"X-User": "arjun"})
    assert b"corporate VPN" in body.content
