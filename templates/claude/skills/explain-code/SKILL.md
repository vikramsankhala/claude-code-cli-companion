---
name: explain-code
description: Explain a file or function for a newcomer, with a diagram of how it fits the project. Use when asked "how does X work?".
argument-hint: "<path or symbol>"
allowed-tools: Read, Grep, Glob
---
Explain `$ARGUMENTS` to a developer who joined the team this week.

1. Find it with Grep and Glob, and read it and its direct callers.
2. Say in two sentences what it does and why it exists.
3. Draw a small Mermaid diagram of the calls in and out.
4. List the two or three things most likely to surprise a newcomer.

Keep it under 300 words. Do not change any files.
