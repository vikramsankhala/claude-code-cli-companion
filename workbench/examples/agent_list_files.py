"""Chapter 40 example: agent_list_files.py. Run: python agent_list_files.py"""
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def main():
    opts = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep"],
        cwd=".",
        max_turns=10,
    )
    async for m in query(prompt="List every .py file here and say what each does.",
                         options=opts):
        if isinstance(m, ResultMessage):
            print(m.result)

asyncio.run(main())
