# <project name>

<One sentence: what this repository is and who uses it.>

## Commands
- Install: `<command>`
- Test: `<command>` (run after every change)
- Lint and format: `<command>`
- Run locally: `<command>`

## Layout
- `<folder>/`: <what lives here>
- `<folder>/`: <what lives here>

## Conventions
- <naming, style, error handling, logging>
- New behaviour needs a test in the same commit.
- Small commits with imperative messages.

## Never
- Never read or edit `.env*` or anything in `secrets/`.
- Never push to `main` directly.
- Never add a dependency without asking first.

Keep this file under 60 lines. Put folder-specific rules in `.claude/rules/*.md` with `paths:` frontmatter, and personal notes in `CLAUDE.local.md` (git-ignored).
