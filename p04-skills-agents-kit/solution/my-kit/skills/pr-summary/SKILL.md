---
name: pr-summary
description: Summarise the current pull request for a reviewer. Use when asked for a PR summary or review notes.
argument-hint: "[focus]"
allowed-tools: Bash(gh *)
context: fork
---
## Context
- Pull request: !`gh pr view --json number,title,author,baseRefName,headRefName`
- Diff: !`gh pr diff`

## Task
Write a summary a busy reviewer can read in one minute:

1. **What changes** in three bullets or fewer, in plain words.
2. **Risk**: low, medium or high, with one sentence of reasoning.
3. **Files to read first**: at most three, each with why.
4. **Questions for the author**, if any.

Focus especially on: $ARGUMENTS
