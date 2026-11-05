# n8n workflows for coding agents

Four importable workflows for **Chapters 19–20** of the book, one per integration pattern, plus start scripts for a local n8n that can run `claude` and `codex`.

| File | Pattern | What it does | Needs |
| --- | --- | --- | --- |
| [`01-ci-failure-summary.json`](workflows/01-ci-failure-summary.json) | **A** · n8n runs the agent | Weekdays 07:41: Claude Code in plan mode summarises failed CI runs; a Code node parses the JSON; Slack gets the summary, or an alert if the run failed | n8n on the agent host, `gh`, Slack |
| [`02-issue-triage.json`](workflows/02-issue-triage.json) | **D + A** | New GitHub issue → a local Mistral model labels it → for bugs, `codex exec --sandbox read-only` names the likely files → Slack, with an "Open in Claude Code" link for the engineer on duty | GitHub, Ollama, Codex, Slack |
| [`03-morning-brief.json`](workflows/03-morning-brief.json) | **D** · an agent inside n8n | Weekdays 08:23: open pull requests from the GitHub API → a local model writes an eight-bullet brief → email. No shell at all | GitHub, Ollama, SMTP |
| [`04-mcp-agent-tools.json`](workflows/04-mcp-agent-tools.json) | **B** · the agent calls n8n | An MCP Server Trigger exposing two pre-approved tools to Claude Code and Codex: `create_ticket` (validated, refuses credentials) and `order_status` (calls the [Shopkeeper](../../labs/practice-app) API) | Nothing external |

Pattern **C** (agents build workflows) is how these files were made: edit the JSON with Claude Code or Codex, review the diff, import. The Sutra nightly-evals workflow is in [`../../part11-sutra-erp/n8n`](../../part11-sutra-erp/n8n).

## 1. Start n8n where the agents live

Execute Command runs inside whatever runs n8n, so for workflows 01 and 02 run n8n with npm on the machine that has `claude` and `codex`:

```bash
./scripts/start-n8n.sh          # macOS, Linux
```

```powershell
.\scripts\start-n8n.ps1         # Windows PowerShell
```

Both set `NODES_EXCLUDE="[]"` to re-enable Execute Command (off by default from n8n 2.0). **Only do this on a machine you trust**, bound to localhost. Workflows 03 and 04 need no shell; for those, the Docker command in Chapter 19 is fine.

## 2. Import

In the editor: **Workflows › Import from file**. Or from the command line:

```bash
n8n import:workflow --separate --input=workflows/
```

Then open each workflow and:

1. Pick your credentials on every node with a red warning (GitHub, Slack, SMTP, Ollama). The files contain **no credentials**; n8n asks you to choose or create them.
2. Replace the placeholders: `your-org/shop`, `$HOME/repos/shop`, the Slack channels, `lead@example.com`.
3. Run once with **Execute workflow** before activating.

If import reports an unknown node version, your n8n is older than the file: open the node, pick the latest version offered and re-enter the fields.

## 3. Connect agents to workflow 04

Activate it and copy the **Production URL** from the MCP Server Trigger (it ends in `/mcp/shop-tools`). Create a bearer credential on the trigger and export the same token in your shell as `N8N_MCP_TOKEN`.

```bash
claude mcp add --transport http shop-tools http://localhost:5678/mcp/shop-tools \
  --header "Authorization: Bearer $N8N_MCP_TOKEN"
```

```toml
# ~/.codex/config.toml
[mcp_servers.shop-tools]
url = "http://localhost:5678/mcp/shop-tools"
bearer_token_env_var = "N8N_MCP_TOKEN"
```

Start the Shopkeeper API (`python -m shopkeeper.server` in `labs/practice-app`) and ask: "What is the status of ORD-1003? If it is on hold, open a high-priority ticket for the accounts team."

## Safety rules built into these files

- Every Claude Code call has `--permission-mode plan`, a short `--allowedTools` list and `--max-turns`; every Codex call has `--sandbox read-only`. No workflow lets an agent change code: a person presses Enter.
- Model output is parsed defensively and forced onto an allow-list of labels before anything acts on it.
- Untrusted text (issue bodies) goes to the model in a prompt, never into a shell command.
- The MCP tools are narrow business actions, not raw API access. `create_ticket` validates its input and refuses anything that looks like a credential.

## Tests

```bash
pip install -r requirements.txt
python -m pytest -q
```

n8n itself cannot run in CI here, so the tests check each file's structure: valid JSON, unique node names, every connection pointing at a real node, every node reachable from the trigger, the guardrail flags on every agent command, no credentials or keys anywhere, and that this README lists every workflow.
