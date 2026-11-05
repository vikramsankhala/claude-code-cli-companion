# P6 · Capstone: ship a feature with parallel agents

Book: Project P6 (Part X), using everything from Parts I to IV.

**Goal.** Deliver a small feature end to end the way a senior engineer would with Claude Code: plan, split, run agents in parallel, review, merge, reflect.

| File | Use |
| --- | --- |
| `templates/PLAN.md` | Fill in: goal, 2 or 3 tasks that do not share files, risks, done criteria |
| `example/PLAN.md` | A worked plan for `sample-app`: bulk discounts and a receipt |
| `scripts/check_plan.py` | Checks the plan is ready: catches shared files, missing done criteria, bad task names |
| `scripts/start_tasks.py` | Starts one `claude -w <task> --bg` agent per task (`--dry-run` prints the commands) |
| `templates/REVIEW-CHECKLIST.md` | What to do in each worktree before merging |
| `templates/RETRO.md` | The 200-word retrospective |

## Do it

```bash
cd your-practice-repo                      # a copy of sample-app with the P1–P5 set-up
claude --permission-mode plan              # plan; save the result as PLAN.md
python path/to/p06-parallel-agents/scripts/check_plan.py PLAN.md
python path/to/p06-parallel-agents/scripts/start_tasks.py PLAN.md
claude agents                              # watch both; attach when one needs you
```

Then review each worktree with the checklist, merge, run the P5 reviewer, open the PR, and write the retrospective with the cost from `/usage`.

## Test the scripts

```bash
python -m pytest -q
```
