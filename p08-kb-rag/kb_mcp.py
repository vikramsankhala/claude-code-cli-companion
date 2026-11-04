"""MCP server: lets Claude Code search the knowledge base as a tool.
Register:  claude mcp add --transport stdio kb -- python /path/to/kb_mcp.py"""
import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from kb import store
from kb.embed import get_embedder
from kb.search import hybrid_search

HERE = Path(__file__).resolve().parent
server = MCPServer("enterprise-kb")
DB_PATH = os.getenv("KB_DB", str(HERE / "kb.sqlite"))
EMB = get_embedder()


@server.tool()
def search_knowledge(query: str, k: int = 5) -> str:
    """Search company policies and guides. Returns numbered passages with their source file.
    Cite the source file when you use a passage."""
    db = store.connect(DB_PATH)  # one connection per call: tools run in worker threads
    env = os.getenv("KB_ALLOWED_GROUPS")
    depts = [d for d in env.split(",") if d] if env else \
        [r[0] for r in db.execute("SELECT DISTINCT dept FROM chunks")]
    hits = hybrid_search(db, EMB, query, depts, min(k, 10))
    if not hits:
        return "No matching passages."
    return "\n\n".join(f"[{i}] source: {h['doc']}\n{h['text']}" for i, h in enumerate(hits, 1))


if __name__ == "__main__":
    server.run()
