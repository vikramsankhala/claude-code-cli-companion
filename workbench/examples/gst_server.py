"""Chapter 39 example. Register with: claude mcp add gst -- python gst_server.py"""
from mcp.server.mcpserver import MCPServer
server = MCPServer("Finance tools")

@server.tool()
def gst(amount_inr: float, rate: float = 18.0) -> float:
    """Return the amount including GST."""
    return round(amount_inr * (1 + rate / 100), 2)

if __name__ == "__main__":
    server.run()
