# Contributing

Thank you for helping improve the companion code for *Claude Code CLI: The Reference Book and Cheat Sheet*.

## Ways to help

- **Report a problem**: a failing test, a step in the book that does not work, a broken link. Use the issue templates.
- **Fix something**: open a pull request with a short description and a test that shows the fix.
- **Suggest an improvement**: open an issue first for larger changes, so we can agree the approach.

## Before you open a pull request

1. Work on a branch: `git switch -c fix/short-description`.
2. Run the tests for the project you changed, or everything with `./scripts/test-all.sh` (or `.\scripts\test-all.ps1` on Windows).
3. Keep each project runnable offline; add new settings as environment variables with safe defaults.
4. Never commit keys, tokens or real personal data. Sample data must be fictional.
5. Write in British English, in plain words, to match the book.

## Using coding agents

You are welcome to use Claude Code, Codex or other agents. You are responsible for every line you submit: read the diff, run the tests and explain the change in your own words.

By contributing you agree that your contribution is licensed under the [MIT License](LICENSE).
