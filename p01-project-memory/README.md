# P1 · Team-ready project memory

Book: Project P1 (Part X), building on Chapter 6.

**Goal.** New joiners, human or agent, learn the repository's commands, conventions and "never" list in one read.

## Do it

1. Copy `../sample-app` to a practice folder and open it in Claude Code (see `sample-app/README.md`).
2. Run `/init`, then cut `CLAUDE.md` to under 60 lines with **Commands**, **Conventions** and **Never** sections.
3. Move API-only rules to `.claude/rules/api.md` with `paths:` frontmatter.
4. Put personal notes in `CLAUDE.local.md` and confirm it is git-ignored.
5. In a fresh session ask: "How do I run the tests, and what must I never edit?"

## Check your work

```bash
python check.py /path/to/your/practice/repo     # Windows: python check.py $HOME\Projects\shop-practice
```

`solution/` holds a reference answer. Compare after you have written your own.
