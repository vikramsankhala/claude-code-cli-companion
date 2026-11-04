"""Source connectors: pull records from external systems into the DMS pipeline.

Every connector yields Items. The platform turns each Item into a DMS document
(new or a new version), so external content gets the same review, versioning,
access control and retention as uploaded files.
"""
import importlib
import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass
class Item:
    ext_id: str          # stable ID in the source system
    title: str
    body: str
    updated: str         # ISO-8601 timestamp from the source; drives incremental sync
    url: str = ""


class SqlSource:
    """Any database with a Python DB-API driver: PostgreSQL (psycopg), MySQL (pymysql),
    SQL Server (pyodbc), Oracle (oracledb), or SQLite for tests.

    config: {"driver": "psycopg", "dsn_env": "CRM_DSN", "query": "...", "columns": {...}}
    The query must accept one parameter: the last sync watermark."""

    def __init__(self, cfg):
        self.cfg = cfg

    def connect(self):
        driver = importlib.import_module(self.cfg["driver"])
        return driver.connect(os.environ[self.cfg["dsn_env"]])  # credentials stay in the environment

    def fetch(self, since: str):
        cols = self.cfg["columns"]
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute(self.cfg["query"], (since,))
            names = [d[0] for d in cur.description]
            for row in cur.fetchall():
                r = dict(zip(names, row))
                yield Item(ext_id=str(r[cols["id"]]), title=str(r[cols["title"]]), body=str(r[cols["body"]]),
                           updated=str(r[cols["updated"]]), url=str(r.get(cols.get("url", ""), "") or ""))
        finally:
            conn.close()


class HttpJsonSource:
    """REST APIs that return JSON pages: wikis, intranets, ticketing and CRM systems.

    config: {"url": "https://wiki.example.com/api/pages", "token_env": "WIKI_TOKEN",
             "items": "results", "next": "next", "since_param": "updated_since",
             "fields": {"id": "id", "title": "title", "body": "body", "updated": "updated_at", "url": "link"}}"""

    def __init__(self, cfg):
        self.cfg = cfg

    def _get(self, url):
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        if self.cfg.get("token_env"):
            req.add_header("Authorization", f"Bearer {os.environ[self.cfg['token_env']]}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())

    def fetch(self, since: str):
        f = self.cfg["fields"]
        url = self.cfg["url"]
        if since and self.cfg.get("since_param"):
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode({self.cfg["since_param"]: since})
        pages = 0
        while url and pages < self.cfg.get("max_pages", 100):  # follow pagination, with a safety cap
            data = self._get(url)
            for r in data[self.cfg["items"]]:
                yield Item(ext_id=str(r[f["id"]]), title=r[f["title"]], body=r[f["body"]],
                           updated=r[f["updated"]], url=r.get(f.get("url", ""), ""))
            url = data.get(self.cfg.get("next", "next"))
            pages += 1


CONNECTORS = {"sql": SqlSource, "http": HttpJsonSource}


def build(cfg):
    return CONNECTORS[cfg["type"]](cfg)
