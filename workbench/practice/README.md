# Six weeks of daily practice: starter and reference files

Book: Chapter 43, with Chapters 40 to 42.

Do the exercises in the book first, typing the commands yourself. Use these files to check your work or to recover if you get stuck.

| File | Day | What it is |
| --- | --- | --- |
| `fintech/emi.py` | 12, 15, 17, 18 | The EMI calculator after weeks 3 and 4: zero-rate fix, rate table and amortisation schedule |
| `fintech/test_emi.py` | 13, 17, 18 | Five tests, including the zero-rate case and a schedule that closes to the paisa |
| `fintech/.gitignore` | 14 | What to keep out of Git |
| `powershell/profile.ps1` | 6, week 4 and 5 reviews | `work`, `research`, `books`, `where-am-i`, `today` and `netcheck` shortcuts |
| `powershell/netcheck.ps1` | Week 5 review | Private IP, gateway, DNS, public IP, ping and HTTPS check in one screen |
| `powershell/backup.ps1` | Week 6 review | Nightly backup with robocopy, skipping `.venv` and caches |
| `powershell/greet.ps1` | Chapter 42 | The smallest useful script with a parameter |

```powershell
cd fintech
python -m pytest -q          # 5 passed
python emi.py                # EMI: ₹8,997.26
```

To use a PowerShell script, copy it to `$HOME\work\scripts\`, then run it with `.\netcheck.ps1`. If Windows blocks it, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once (Chapter 40).
