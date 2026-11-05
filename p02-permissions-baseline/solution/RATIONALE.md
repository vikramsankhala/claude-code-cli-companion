# Why each deny rule exists

- **`Read(./.env)` and `Read(./.env.*)`**: environment files hold keys and passwords. Claude never needs their values to write code; it needs the variable names, which live in `.env.example`.
- **`Read(./secrets/**)` and `Edit(./secrets/**)`**: signing keys and certificates must not enter a model's context or be changed by an agent, even by accident.
- **`Bash(rm -rf *)`**: recursive deletion is never routine. A person can run it; an agent cannot.
- **`Bash(curl *)`**: stops an agent sending repository content to an arbitrary address. Web lookups go through the WebFetch tool, which has its own controls.
- **`Bash(git push --force *)`**: rewriting shared history is a team decision, never an agent's.

Pushes and installs are in `ask`, not `deny`: they are normal work, but a person should see each one.
