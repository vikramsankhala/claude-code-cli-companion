# Solutions to the planted bugs

Try D1–D3 first. Each fix is one line.

| # | File | Bug | Fix |
| --- | --- | --- | --- |
| 1 | `shopkeeper/catalogue.py` | `start = number * size` skips the first page, because pages are numbered from 1 | `start = (number - 1) * size` |
| 2 | `shopkeeper/pricing.py` | `Decimal(int((net + tax) * 100)) / 100` truncates: 1.239 becomes 1.23 | `return money(net + tax)` (half-up to the paisa) |
| 3 | `shopkeeper/inventory.py` | `if qty >= self.available(sku)` refuses to reserve the last unit | `if qty > self.available(sku)` |

After the fixes, `python -m pytest exercises -q` shows `3 passed`, and `python -m pytest -q` still shows `5 passed`.

What a good D3 session looks like: one bug per turn, each diff one line, the tests run after every change, and nothing under `exercises/` edited.
