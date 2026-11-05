---
paths:
  - "web/**/*.tsx"
  - "web/**/*.ts"
---
# Front-end rules

- Components are function components with typed props; no default exports.
- Fetch data through `web/lib/api.ts`, never directly from a component.
- Every new screen gets a Playwright test in `web/tests/`.
