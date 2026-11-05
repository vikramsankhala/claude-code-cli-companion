---
paths:
  - "shop/api.py"
  - "shop/api/**"
---
# API rules

- Responses are plain dicts that serialise to JSON; money fields are numbers, never strings.
- Every response includes `"currency": "INR"`.
- Keep field names stable: `lines`, `net`, `total`, `currency`. Adding a field is fine; renaming one breaks clients.
- Validate inputs at the boundary and raise `ValueError` with a message a caller can show.
