# P7 · mini-coder: your own coding agent on an open-source model

Book: Project P7 and "How Coding Agents Work Beneath the Hood" (Part X).

A complete coding agent in one file: a chat loop, four tools (list, read, write, run), a sandbox that keeps it inside the current folder, approval prompts and an `AGENTS.md` rules file.

## Run the tests (no model needed)

```bash
pip install -r requirements.txt
python test_agent.py            # the version printed in the book; last line: ALL CHECKS PASSED
python test_agent_extended.py   # extra safety checks
```

## Run it for real

```bash
ollama pull qwen3:8b
cd /path/to/a/small/repo
python /path/to/agent.py "add a unit test for calc.py and run it"
```

| Variable | Default | Meaning |
| --- | --- | --- |
| `MINI_CODER_MODEL` | `qwen3:8b` | Any tool-calling model |
| `MINI_CODER_BASE_URL` | `http://localhost:11434/v1` | Any OpenAI-compatible endpoint (Ollama, vLLM, LiteLLM) |
| `MINI_CODER_MAX_STEPS` | `25` | Upper limit on tool calls per task |
| `MINI_CODER_AUTO_APPROVE` | unset | `1` only in tests |
