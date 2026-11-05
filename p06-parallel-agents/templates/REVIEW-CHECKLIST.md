# Reviewing each worktree before merging

1. `claude attach <id>` or open the worktree, then run `/diff` and read every changed line.
2. Run `/security-review`.
3. Run the tests in the worktree: `python -m pytest -q`.
4. Check the task stayed inside its files in PLAN.md: `git diff --stat main...`.
5. Rewind anything wrong with `/rewind` (or `Esc Esc`) rather than patching over it.
6. Merge one task at a time and run the full suite after each merge.
