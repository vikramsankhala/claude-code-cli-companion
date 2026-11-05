"""Lab 4: tool calling. The model decides to call gst(); your code runs it and returns the result.
Run: python tools.py   (use a model whose page says it supports tool calling)"""
import json

from common import CHAT_MODEL, answer_text, client, with_backoff

TOOLS = [{"type": "function", "function": {
    "name": "gst", "description": "Amount including Indian GST.",
    "parameters": {"type": "object", "properties": {"amount_inr": {"type": "number"}, "rate": {"type": "number"}},
                   "required": ["amount_inr"]}}}]


def gst(amount_inr, rate=18.0):
    return round(amount_inr * (1 + rate / 100), 2)


c = client()
messages = [{"role": "user", "content": "What is 45,000 rupees including GST at 18%? Use the tool."}]
first = with_backoff(lambda: c.chat.completions.create(model=CHAT_MODEL, messages=messages, tools=TOOLS, temperature=0))
msg = first.choices[0].message
if not msg.tool_calls:
    print("The model answered without the tool:", msg.content)
else:
    messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})
    for tc in msg.tool_calls:
        args = json.loads(tc.function.arguments)
        result = gst(**args)
        print(f"tool call: gst({args}) -> {result}")
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
    final = with_backoff(lambda: c.chat.completions.create(model=CHAT_MODEL, messages=messages, temperature=0))
    print(answer_text(final))
