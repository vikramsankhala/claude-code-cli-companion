# test_agent.py  -  run: python test_agent.py
import json, os, subprocess, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXED = "def add(a, b):\n    return a + b\n"
SCRIPT = [  # the fake model's replies, in order
    ("tool", "list_files", {"path": "."}),
    ("tool", "read_file", {"path": "calc.py"}),
    ("tool", "read_file", {"path": "../outside.txt"}),       # must be refused
    ("tool", "run_command", {"command": "sudo rm -rf /"}),   # must be blocked
    ("tool", "write_file", {"path": "calc.py", "content": FIXED}),
    ("tool", "run_command", {"command": "python -m pytest -q"}),
    ("text", "Fixed add() to return a + b; the test passes.", None),
]
seen = []

class FakeModel(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        seen.append(body["messages"])
        kind, name, args = SCRIPT[len(seen) - 1]
        if kind == "tool":
            message = {"role": "assistant", "content": None, "tool_calls": [{
                "id": f"call_{len(seen)}", "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)}}]}
            finish = "tool_calls"
        else:
            message, finish = {"role": "assistant", "content": name}, "stop"
        out = json.dumps({"id": "x", "object": "chat.completion", "created": 0,
                          "model": "fake", "choices": [{"index": 0, "message": message,
                          "finish_reason": finish}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)
    def log_message(self, *a):
        pass

def main():
    server = HTTPServer(("127.0.0.1", 0), FakeModel)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "demo"; proj.mkdir()
        (Path(tmp) / "outside.txt").write_text("SECRET")
        (proj / "calc.py").write_text("def add(a, b):\n    return a - b\n")
        (proj / "test_calc.py").write_text(
            "from calc import add\n\ndef test_add():\n    assert add(2, 3) == 5\n")
        env = dict(os.environ, MINI_CODER_BASE_URL=f"http://127.0.0.1:{server.server_port}/v1",
                   MINI_CODER_MODEL="fake", MINI_CODER_AUTO_APPROVE="1")
        r = subprocess.run([sys.executable, str(HERE / "agent.py"), "fix the failing test"],
                           cwd=proj, env=env, capture_output=True, text=True, timeout=120)
        results = [m["content"] for m in seen[-1] if m.get("role") == "tool"]
        assert "outside the project root" in results[2]
        assert "Blocked by policy" in results[3]
        assert (proj / "calc.py").read_text() == FIXED
        assert "exit code 0" in results[5] and "passed" in results[5]
        assert "Fixed add()" in r.stdout
    server.shutdown()
    print("ALL CHECKS PASSED")

if __name__ == "__main__":
    main()
