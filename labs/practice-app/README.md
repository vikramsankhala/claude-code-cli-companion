# Shopkeeper: the practice app

A small shop back end (catalogue, pricing with GST, inventory, a JSON API) for demos D1–D8. It has **three planted bugs**, each caught by one failing test in `exercises/`.

```bash
python -m pytest -q              # 5 passing tests
python -m pytest exercises -q    # 3 failing tests: your job in D1–D3
python -m shopkeeper.server      # API on http://127.0.0.1:8765/items?page=1
```

Copy this folder somewhere outside the repository and `git init` it before you start, so checkpoints, worktrees and diffs have a clean history:

```bash
cp -r labs/practice-app ~/shopkeeper && cd ~/shopkeeper && git init && git add . && git commit -m "start"
```

```powershell
Copy-Item -Recurse labs\practice-app $HOME\shopkeeper; cd $HOME\shopkeeper; git init; git add .; git commit -m "start"
```

Answers are in [`../SOLUTIONS.md`](../SOLUTIONS.md). Try first.
