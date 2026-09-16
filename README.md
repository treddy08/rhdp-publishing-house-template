# {{ values.project_name }}

{{ values.project_description }}

**Owner:** {{ values.github_user }}

---

## What was set up

1. Repository created
2. `catalog-info.yaml` added to repository
3. Registered in Developer Hub catalog
4. Orchestrator workflow started — your AI-guided content pipeline is running!

## What happens next

Claude will walk you through the entire content lifecycle — from intake and spec creation, through Jira tracking and reviews, all the way to a published lab on RHDP. Just follow the prompts!

## Getting started

### DevSpaces (recommended)

1. Open in DevSpaces: `{{ values.devspaces_url }}#{{ values.repo_url }}`
2. Use Claude via the **extension** or the **CLI**:
   - **Extension:** Click the **Claude** icon in the sidebar, click **New Session**. If the Claude icon is not visible, open **Extensions** (`Ctrl/Cmd+Shift+X`), find **Claude Code for VS Code** under the DevSpaces section, click it, then click **Enable (Workspace)**.
   - **CLI:** Open a terminal and run `claude`
3. Run `/rhdp-publishing-house` — and you're off!

### Local machine

1. Clone the repo:
   ```
   git clone {{ values.repo_url }}
   ```
2. `cd {{ values.project_name }}`
3. Start Claude CLI: `claude`
4. Run `/rhdp-publishing-house` — and you're off!
