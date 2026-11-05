"""A local MCP server with one tool only it can answer: the status of a Shopkeeper order.
Register (from the repository root):
  claude mcp add --transport stdio shop-orders -- python labs/d08-live-tool/orders_mcp.py
Codex:
  codex mcp add shop-orders -- python labs/d08-live-tool/orders_mcp.py"""
import sys
from pathlib import Path

from mcp.server.mcpserver import MCPServer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "practice-app"))
from shopkeeper.orders import ORDERS  # noqa: E402

server = MCPServer("shop-orders")


@server.tool()
def order_status(order_id: str) -> str:
    """Look up a Shopkeeper order by id (for example ORD-1001): customer, status, courier and ETA."""
    o = ORDERS.get(order_id.strip().upper())
    if o is None:
        return f"No order {order_id}. Known ids: {', '.join(sorted(ORDERS))}"
    lines = ", ".join(f"{q} x {sku}" for sku, q in o["lines"])
    return (f"{order_id}: {o['customer']} · {o['status']} · {lines} · courier {o['courier'] or 'not assigned'}"
            f" · ETA {o['eta'] or 'unknown'}")


if __name__ == "__main__":
    server.run()
