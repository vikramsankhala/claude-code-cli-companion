# P4 · Personal skills and agents kit

Book: Project P4 (Part X), building on Chapter 10.

**Goal.** Package the three things you ask Claude for most, and share them as a plugin.

| Piece | File | Key settings |
| --- | --- | --- |
| `/pr-summary [focus]` | `skills/pr-summary/SKILL.md` | `!`gh pr diff`` context, `context: fork`, `allowed-tools: Bash(gh *)` |
| `/release-notes <from> <to>` | `skills/release-notes/SKILL.md` | `$0` and `$1`, `disable-model-invocation: true` |
| `test-runner` subagent | `agents/test-runner.md` | `tools: Bash, Read, Edit, Grep, Glob`, `model: sonnet` |
| Plugin manifest | `.claude-plugin/plugin.json` | name, version, description |

## Use it

```bash
claude --plugin-dir ./solution/my-kit        # try the whole kit as a plugin in this session
```

Or install the pieces personally:

```powershell
Copy-Item -Recurse solution\my-kit\skills\* $HOME\.claude\skills\
Copy-Item solution\my-kit\agents\test-runner.md $HOME\.claude\agents\
```

Then run `/skills` and `/skill-doctor` to see them and their token cost. `/pr-summary` needs the GitHub CLI (`gh`) and an open pull request.

## Check your own kit

```bash
pip install -r requirements.txt
python check.py path/to/your-kit
```
