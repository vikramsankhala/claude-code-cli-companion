# Shopkeeper (practice app for the guided demos)

- Python 3.11+, standard library only. Tests: `python -m pytest -q` (passing) and `python -m pytest exercises -q` (three planted failures).
- Money is `Decimal`, rounded half-up to the paisa. Never use float for totals.
- Pages in the API are numbered from 1.
- Do not edit files under `exercises/`: the tests there are the specification.
