"""REST API:  uvicorn api:app --reload   then open http://127.0.0.1:8000/docs
Identity comes from the X-User header here; in production use your SSO (OIDC) gateway."""
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse

from dms.service import DMS, AccessDenied, load_users

app = FastAPI(title="Document Management API")
dms = DMS(os.getenv("DMS_ROOT", "stores"))
USERS = load_users(os.getenv("DMS_USERS", "users.json"))


def who(x_user: str):
    if x_user not in USERS:
        raise HTTPException(401, "Unknown user")
    return USERS[x_user]


def guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except AccessDenied as e:
        raise HTTPException(403, str(e))
    except KeyError as e:
        raise HTTPException(404, f"Not found: {e}")
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/search")
def search(q: str, x_user: str = Header()):
    return [{k: d[k] for k in ("id", "title", "status", "language", "region", "current_version", "snip")}
            for d in guard(dms.search, who(x_user), q)]


@app.get("/documents/{doc_id}")
def meta(doc_id: str, x_user: str = Header()):
    return guard(dms.get, who(x_user), doc_id)


@app.get("/documents/{doc_id}/versions/{version}/content")
def content(doc_id: str, version: int, x_user: str = Header()):
    d = guard(dms.get, who(x_user), doc_id, version)
    return FileResponse(d["path"], filename=d["filename"])


@app.post("/documents", status_code=201)
async def upload(file: UploadFile = File(...), title: str = Form(...), doc_type: str = Form(...),
                 entity: str = Form(...), region: str = Form(...), dept: str = Form(...),
                 language: str = Form(...), classification: str = Form("internal"),
                 x_user: str = Header()):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / Path(file.filename).name
        path.write_bytes(await file.read())
        doc_id = guard(dms.register, who(x_user), path, title=title, doc_type=doc_type, entity=entity,
                       region=region, dept=dept, language=language, classification=classification)
    return {"id": doc_id}


@app.post("/documents/{doc_id}/status/{new}")
def status(doc_id: str, new: str, x_user: str = Header()):
    guard(dms.set_status, who(x_user), doc_id, new)
    return {"id": doc_id, "status": new}
