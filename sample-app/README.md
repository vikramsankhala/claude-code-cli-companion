# sample-app · the practice repository for Projects P1 to P6

A deliberately small Python package (a shop's cart, pricing and an order API stub) used as the target for Projects P1 to P6. Copy it somewhere outside this repository before you start, so each project begins clean:

```powershell
Copy-Item -Recurse sample-app $HOME\Projects\shop-practice     # Windows
cd $HOME\Projects\shop-practice; git init; git add .; git commit -m "Start"
```

```bash
cp -r sample-app ~/Projects/shop-practice                        # macOS, Linux
cd ~/Projects/shop-practice && git init && git add . && git commit -m "Start"
```

| Command | Purpose |
| --- | --- |
| `python -m pytest -q` | Run the tests (the "fast suite" the P3 hooks call) |
| `ruff check .` · `ruff format .` | Lint and format |
| `python -m shop.api` | Print a sample order as JSON |

`secrets/` and `.env.example` exist so P2 has something to protect. They contain only fake values.
