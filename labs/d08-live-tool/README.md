# D8 · Connect a live tool (15 min)

**Feature:** `claude mcp add`, `/mcp` · **Book:** Part X, Guided Demos; Chapter 9

## Steps: a local server first

1. Install the one dependency: `pip install -r labs/requirements.txt`
2. From the repository root, register the server for this project:
   ```bash
   claude mcp add --transport stdio shop-orders -- python labs/d08-live-tool/orders_mcp.py
   ```
3. Start `claude`, run `/mcp` and check `shop-orders` is **connected**.
4. Ask a question only the tool can answer:
   > Why is ORD-1003 not dispatched yet, and what should I tell the customer?

## Then a remote one

Add an HTTP server for a service you already use (a docs site or an issue tracker that publishes an MCP endpoint), then sign in from `/mcp`:

```bash
claude mcp add --transport http <name> <url>
```

## Observe

- Tools appear as `mcp__shop-orders__order_status`; you can allow or deny them by that name in settings (Chapter 7).
- Claude calls the tool, quotes its answer ("on hold: GSTIN mismatch") and only then reasons about it.
- `claude mcp list` shows the scope (local, project or user). Use `--scope project` to share it through `.mcp.json`.

Official: [MCP quickstart](https://code.claude.com/docs/en/mcp-quickstart)
