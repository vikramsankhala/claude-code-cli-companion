"""One MCP server for Claude Code: search documents, retrieve knowledge, read metadata.
Register: claude mcp add --transport stdio kmp --env KMP_USER=priya -- python /path/to/kmp_mcp.py"""
import os
from pathlib import Path

from kmp.core import Platform
from mcp.server.mcpserver import MCPServer

ROOT = os.getenv("KMP_ROOT", str(Path(__file__).resolve().parent / "data"))
server = MCPServer("knowledge-platform")


def _ctx():
    kp = Platform(ROOT, os.getenv("DMS_USERS", str(Path(__file__).resolve().parent / "users.json")))
    return kp, kp.users[os.getenv("KMP_USER", "priya")]  # per call: tools run in worker threads


@server.tool()
def search_documents(query: str) -> str:
    """Find documents. Supports words plus filters such as type:contract lang:de status:approved region:eu."""
    kp, user = _ctx()
    rows = kp.dms.search(user, query)
    return "\n".join(f"{d['id']} v{d['current_version']} [{d['status']}, {d['language']}] {d['title']}"
                     for d in rows) or "No documents found."


@server.tool()
def retrieve_knowledge(question: str) -> str:
    """Return approved passages that answer a question, in any language, each with its document ID."""
    kp, user = _ctx()
    hits = kp.retrieve(user, question)
    return "\n\n".join(f"[{i}] {h['doc']} · {h['title']}\n{h['text']}" for i, h in enumerate(hits, 1)) \
        or "No approved passages found."


@server.tool()
def document_details(doc_id: str) -> str:
    """Metadata and version history for one document ID, for example EU-000001."""
    kp, user = _ctx()
    d = kp.dms.get(user, doc_id)
    hist = kp.dms.history(user, doc_id)
    keys = ("id", "title", "doc_type", "entity", "region", "language", "classification", "status",
            "current_version", "retention_until", "legal_hold")
    return "\n".join(f"{k}: {d[k]}" for k in keys) + "\nversions: " + \
        "; ".join(f"v{h['version']} {h['created_utc']} {h['note']}" for h in hist)


if __name__ == "__main__":
    server.run()
