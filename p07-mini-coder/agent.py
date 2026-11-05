"""mini-coder: a small coding agent that runs on an open-source LLM via Ollama.

Run:  python agent.py            (interactive)
      python agent.py "task"     (one task, then exit)
"""
import difflib
import json
import os
import subprocess
import sys
from pathlib import Path

from openai import OpenAI

# ---------------------------------------------------------------- 1. Config
MODEL = os.getenv("MINI_CODER_MODEL", "qwen3:8b")
BASE_URL = os.getenv("MINI_CODER_BASE_URL", "http://localhost:11434/v1")
MAX_STEPS = int(os.getenv("MINI_CODER_MAX_STEPS", "25"))
AUTO_APPROVE = os.getenv("MINI_CODER_AUTO_APPROVE") == "1"  # for tests only
ROOT = Path.cwd().resolve()  # the agent may only touch files under here

client = OpenAI(base_url=BASE_URL, api_key="ollama")  # key required, ignored

# Commands that run without asking (read-only or test commands).
SAFE_PREFIXES = ("ls", "cat ", "pwd", "git status", "git diff", "git log",
                 "python -m pytest", "pytest", "npm test", "grep ")
# Commands that never run, whatever the user says.
BLOCKED = ("rm -rf /", "rm -rf ~", "sudo ", "git push --force", ":(){", "mkfs")


# ---------------------------------------------------------------- 2. Safety helpers
def safe_path(rel: str) -> Path:
    """Resolve a path and refuse anything outside the project root."""
    p = (ROOT / rel).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError(f"Path {rel!r} is outside the project root")
    return p


def confirm(question: str) -> bool:
    if AUTO_APPROVE:
        return True
    return input(f"\n{question} [y/N] ").strip().lower() == "y"


# ---------------------------------------------------------------- 3. Tools
def list_files(path: str = ".") -> str:
    base = safe_path(path)
    skip = {".git", ".venv", "node_modules", "__pycache__"}
    out = []
    for p in sorted(base.rglob("*")):
        if any(part in skip for part in p.parts):
            continue
        if p.is_file():
            out.append(str(p.relative_to(ROOT)))
        if len(out) >= 200:
            out.append("... (truncated at 200 files)")
            break
    return "\n".join(out) or "(no files)"


def read_file(path: str) -> str:
    text = safe_path(path).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    numbered = [f"{i + 1:4d} | {line}" for i, line in enumerate(lines[:400])]
    if len(lines) > 400:
        numbered.append(f"... ({len(lines) - 400} more lines)")
    return "\n".join(numbered)


def write_file(path: str, content: str) -> str:
    p = safe_path(path)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    diff = "".join(difflib.unified_diff(old.splitlines(True), content.splitlines(True),
                                        fromfile=f"a/{path}", tofile=f"b/{path}"))
    print(f"\n--- proposed change to {path} ---\n{diff or '(no change)'}")
    if not confirm(f"Write {path}?"):
        return "User declined the write. Ask what to change."
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {path} ({len(content)} chars)."


def run_command(command: str) -> str:
    if any(b in command for b in BLOCKED):
        return "Blocked by policy. Do not retry this command."
    if not command.startswith(SAFE_PREFIXES) and not confirm(f"Run `{command}`?"):
        return "User declined the command."
    try:
        r = subprocess.run(command, shell=True, cwd=ROOT, capture_output=True,  # nosemgrep: subprocess-shell-true (an agent shell tool, behind BLOCKED and confirm)
                           text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return "Command timed out after 120 s."
    out = (r.stdout + r.stderr)[-4000:]  # keep the tail: errors are usually last
    return f"exit code {r.returncode}\n{out}"


TOOLS = {"list_files": list_files, "read_file": read_file,
         "write_file": write_file, "run_command": run_command}

# JSON Schemas tell the model what each tool does and what arguments it takes.
TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "list_files", "description": "List project files under a directory.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Directory, default '.'"}}}}},
    {"type": "function", "function": {
        "name": "read_file", "description": "Read a text file with line numbers.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Create or overwrite a file with the COMPLETE new content.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "run_command",
        "description": "Run a shell command in the project root, e.g. tests.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string"}}, "required": ["command"]}}},
]


# ---------------------------------------------------------------- 4. System prompt
def system_prompt() -> str:
    prompt = (
        "You are mini-coder, a careful coding agent working in the project at "
        f"{ROOT}. Use the tools to inspect files before changing them. "
        "Make the smallest change that solves the task. After editing code, "
        "run the tests. When finished, reply with a short summary of what you "
        "changed and why. Never invent file contents you have not read."
    )
    rules = ROOT / "AGENTS.md"  # project instructions, like CLAUDE.md
    if rules.exists():
        prompt += "\n\nProject instructions:\n" + rules.read_text(encoding="utf-8")
    return prompt


# ---------------------------------------------------------------- 5. The agent loop
def run_tool(name: str, raw_args: str) -> str:
    try:
        args = json.loads(raw_args or "{}")
        return TOOLS[name](**args)
    except KeyError:
        return f"Unknown tool {name!r}."
    except Exception as e:  # report errors back so the model can recover
        return f"Tool error: {type(e).__name__}: {e}"


def agent_turn(messages: list) -> str:
    for step in range(1, MAX_STEPS + 1):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOL_SCHEMAS, temperature=0.2)
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:  # no tool requested: the model has answered
            return msg.content or ""
        for call in msg.tool_calls:
            print(f"  [{step}] {call.function.name}({call.function.arguments[:80]})")
            result = run_tool(call.function.name, call.function.arguments)
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": result})
    return f"Stopped after {MAX_STEPS} steps without finishing."


def main() -> None:
    messages = [{"role": "system", "content": system_prompt()}]
    if len(sys.argv) > 1:
        messages.append({"role": "user", "content": " ".join(sys.argv[1:])})
        print(agent_turn(messages))
        return
    print(f"mini-coder on {MODEL} in {ROOT}. Type 'exit' to quit.")
    while True:
        task = input("\n> ").strip()
        if task in {"exit", "quit"}:
            break
        if task:
            messages.append({"role": "user", "content": task})
            print("\n" + agent_turn(messages))


if __name__ == "__main__":
    main()
