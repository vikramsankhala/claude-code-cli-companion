---
name: kb-gap-writer
description: Draft knowledge articles for questions the platform could not answer. Use after the nightly knowledge-gap report.
allowed-tools: Read, Write, Bash(python kmp_cli.py search *)
---
## Context
- Unanswered questions: !`cat data/reports/knowledge-gaps.md 2>/dev/null || echo "No report yet"`

For each of the top 5 questions:
1. Run `python kmp_cli.py search "<keywords>"` to confirm no approved document covers it.
2. Draft a short Markdown article in `drafts/<region>/<dept>/<slug>.md`, in the language the question was asked in.
3. Start the file with a level-1 title. Mark every fact you could not verify with `TODO: verify`.

Finish with a table: question, draft path, open TODOs. Drafts go to the inbox only after a human edits them.
