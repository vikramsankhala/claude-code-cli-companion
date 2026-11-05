"""A tiny OpenAI-compatible server for offline tests. It records every request so tests can
check what the scripts send, and it can return a 429 first to exercise the back-off."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class Fake:
    def __init__(self):
        self.requests = []
        self.fail_first = 0
        self.server = HTTPServer(("127.0.0.1", 0), self._handler())
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1"

    def stop(self):
        self.server.shutdown()

    def _handler(self):
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, obj):
                body = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path.endswith("/models"):
                    ids = ["good/chat", "think/reasoner", "gone/retired", "missing/listed", "x/embed-qa", "nvidia/nemotron-3.5-bolt-e4b"]
                    return self._send(200, {"object": "list", "data": [{"id": i, "object": "model", "created": 0, "owned_by": "x"} for i in ids]})
                self._send(404, {"error": {"message": "not found"}})

            def do_POST(self):
                req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                fake.requests.append((self.path, req, self.headers.get("Authorization")))
                if fake.fail_first > 0:
                    fake.fail_first -= 1
                    return self._send(429, {"error": {"message": "rate limited"}})
                if self.path.endswith("/embeddings"):
                    vec = lambda t: [1.0 if w in t.lower() else 0.0 for w in ("password", "invoice", "office")] + [0.1]
                    data = [{"object": "embedding", "index": i, "embedding": vec(t)} for i, t in enumerate(req["input"])]
                    return self._send(200, {"object": "list", "data": data, "model": req["model"],
                                            "usage": {"prompt_tokens": 5, "total_tokens": 5}})
                if req.get("model") == "gone/retired":
                    return self._send(410, {"error": {"message": "gone"}})
                if req.get("model") == "missing/listed":
                    return self._send(404, {"error": {"message": "not found"}})
                model, msgs = req["model"], req["messages"]
                if model == "think/reasoner":
                    msg = {"role": "assistant", "content": None, "reasoning_content": "Let me think..."}
                elif "guard" in model:
                    text = "unsafe S2" if "steal" in msgs[-1]["content"] else "safe"
                    msg = {"role": "assistant", "content": text}
                elif req.get("tools") and msgs[-1]["role"] == "user":
                    msg = {"role": "assistant", "content": "", "tool_calls": [{"id": "call_1", "type": "function",
                           "function": {"name": "gst", "arguments": json.dumps({"amount_inr": 45000, "rate": 18})}}]}
                elif msgs[-1]["role"] == "tool":
                    msg = {"role": "assistant", "content": f"It comes to {msgs[-1]['content']} rupees."}
                else:
                    msg = {"role": "assistant", "content": f"[{model}] An API lets programs talk to each other."}
                if req.get("stream"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.end_headers()
                    for word in msg["content"].split(" "):
                        chunk = {"id": "c", "object": "chat.completion.chunk", "created": 0, "model": model,
                                 "choices": [{"index": 0, "delta": {"content": word + " "}, "finish_reason": None}]}
                        self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
                    self.wfile.write(b"data: [DONE]\n\n")
                    return
                self._send(200, {"id": "x", "object": "chat.completion", "created": 0, "model": model,
                                 "choices": [{"index": 0, "message": msg, "finish_reason": "stop"}],
                                 "usage": {"prompt_tokens": 12, "completion_tokens": 9, "total_tokens": 21}})
        return H
