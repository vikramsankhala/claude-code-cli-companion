# P9 · Multinational document management, indexing, retrieval and querying

Book: Project P9.

Regional stores (`in`, `eu`, `us`) with content-addressed versions, classification, a review workflow, retention and legal hold, an audit log, a query language and a FastAPI service.

```bash
pip install -r requirements.txt
python -m pytest -q                                  # 7 passed

python dms_cli.py --user priya register leave-policy.pdf --title "Leave policy" --type policy \
  --entity "Acme India Pvt Ltd" --region in --dept hr --lang en --class internal
python dms_cli.py --user priya search 'leave status:approved type:policy region:in'
uvicorn api:app --reload                             # then open http://localhost:8000/docs
```

Run `python dms_cli.py --help` for every command. Sample users and their regions and clearances are in `users.json` (`priya`, `arjun`, `lena`, `mike`).

| Variable | Default | Meaning |
| --- | --- | --- |
| `DMS_ROOT` | `stores` | Where the regional stores live |
| `DMS_USERS` | `users.json` | User directory |
| `DMS_USER` | `priya` | Acting user for the CLI |
