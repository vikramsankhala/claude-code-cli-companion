"""A tiny JSON API on the standard library. Run: python -m shopkeeper.server  (port 8765)
GET /items?page=1   list products, three per page
GET /items/<sku>    one product
GET /orders/<id>    one order (used by the n8n MCP tool in automation/n8n)
Demo D5 adds GET /health."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from . import catalogue
from .orders import ORDERS


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802 (name fixed by http.server)
        url = urlparse(self.path)
        if url.path == "/items":
            n = int(parse_qs(url.query).get("page", ["1"])[0])
            return self._send(200, catalogue.page(catalogue.ITEMS, n))
        if url.path.startswith("/items/"):
            try:
                return self._send(200, catalogue.find(url.path.split("/", 2)[2]))
            except KeyError as e:
                return self._send(404, {"error": str(e)})
        if url.path.startswith("/orders/"):
            oid = url.path.split("/", 2)[2].upper()
            if oid in ORDERS:
                return self._send(200, {"id": oid, **ORDERS[oid]})
            return self._send(404, {"error": f"unknown order {oid!r}"})
        return self._send(404, {"error": "not found"})

    def log_message(self, *args):  # keep test output quiet
        pass


def serve(port: int = 8765) -> HTTPServer:
    return HTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    print("Shopkeeper on http://127.0.0.1:8765  (Ctrl+C to stop)")
    serve().serve_forever()
