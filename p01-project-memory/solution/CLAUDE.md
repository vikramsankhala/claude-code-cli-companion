# shop: project memory

A small Python package for carts, pricing and GST. Python 3.11+.

## Commands
- Test: `python -m pytest -q` (fast; run after every change)
- Lint and format: `ruff check --fix .` then `ruff format .`
- Try it: `python -m shop.api`

## Layout
- `shop/pricing.py`: GST rates and discounts. Money in rupees, rounded to the paisa.
- `shop/cart.py`: the `Cart` dataclass.
- `shop/api.py`: order summary JSON (API rules in `.claude/rules/api.md`).
- `tests/`: pytest; one test file per module.

## Conventions
- British English in comments and messages.
- Round money with `round(x, 2)` at the boundary, never in the middle of a calculation.
- New behaviour needs a test in the same commit.
- Small commits with imperative messages ("Add reduced GST rate").

## Never
- Never read or edit `.env`, `.env.*` or anything in `secrets/`.
- Never change GST rates without a linked ticket in the commit message.
- Never push to `main` directly; open a pull request.
- Never add a dependency without asking first.

Personal settings (sandbox URLs, local paths) live in `CLAUDE.local.md`, which is git-ignored.
