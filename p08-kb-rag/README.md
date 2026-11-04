# P8 · Multilingual enterprise knowledge base with hybrid RAG

Book: Project P8.

SQLite FTS5 (BM25) plus vector search, fused with Reciprocal Rank Fusion; folder-based access groups; a golden-set evaluation; an MCP server so Claude Code and Codex can search it.

```bash
pip install -r requirements.txt
KB_EMBEDDER=hash python -m pytest -q             # 9 passed, offline

KB_EMBEDDER=hash python kb_cli.py ingest docs     # index the sample documents (English, German, Hindi)
KB_EMBEDDER=hash python kb_cli.py search "travel reimbursement limit"
python kb_cli.py eval eval/golden.jsonl           # recall@5 on the golden set
claude mcp add --transport stdio kb -- python kb_mcp.py
```

Windows PowerShell: set variables with `$env:KB_EMBEDDER = "hash"` before the command.

| Variable | Default | Meaning |
| --- | --- | --- |
| `KB_EMBEDDER` | Ollama | `hash` for offline, deterministic embeddings |
| `KB_EMBED_MODEL` · `KB_CHAT_MODEL` | `bge-m3` · `qwen3:8b` | Models for real embeddings and `ask` |
| `KB_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible endpoint |
| `KB_DB` | `kb.sqlite` | Index file |
| `KB_ALLOWED_GROUPS` | all | Comma-separated access groups, e.g. `global,in/hr` |
