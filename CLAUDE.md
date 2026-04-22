# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered bug fixer that receives incidents from Jira, automatically resolves them using an LLM, and opens pull requests in the correct repository. Development language is **Python only**.

## Architecture

The system has three main components that can all be developed in this single repository:

### 1. Slack Bot (User Interface)
- Listens to slash commands in a Slack group called "AI Resolver"
- `/list-open-incidents` — queries Jira for TODO incidents and returns a list
- `/resolve-incident IN-XXX` — triggers the resolution pipeline for a specific incident

### 2. Incident Processor Server
- Receives incident descriptions forwarded from the Slack bot
- Uses a local LLM (managed by Claude Code or another LLM manager) to analyze the incident
- Identifies the target repository, clones it if not already present (via `git clone`)
- Applies the fix and pushes to the repo
- Opens PRs to three branches: `master`, `stage`, and `integration`

### 3. MCP Integration Layer
- MCP (Model Context Protocol) is the **primary** integration method for all tools
- Fall back to traditional REST APIs only when no MCP integration exists for a tool
- Tools to integrate: Slack, Jira, GitHub, Linux filesystem, Git client, LLM provider

### Data Flow
```
Slack command (/resolve-incident IN-XXX)
    → Jira (fetch incident description for IN-XXX)
    → MCP Server → Local LLM (identify repo + generate fix)
    → Git clone (if repo not present locally)
    → Apply fix to codebase
    → Open PRs to master, stage, integration
    → Notify user on Slack
```

## Development Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in credentials
cp .env.example .env

# Run tests
pytest

# Lint
ruff check .
```

## Running the Services

Both services must run simultaneously. Start the MCP server first, then the Slack bot.

```bash
# 1. MCP Incident Processor Server (default: localhost:8080)
python -m mcp_server.server

# 2. Slack Bot (Socket Mode — no public URL needed)
python -m slack_bot.app
```

## Project Structure

```
ai-bug-fixer/
├── config.py                        # All env-var config, loaded via python-dotenv
├── mcp_server/
│   └── server.py                    # MCP SSE server — exposes list_open_incidents + process_incident tools
├── incident_processor/
│   ├── processor.py                 # Anthropic agentic loop — the core LLM-driven fix engine
│   ├── jira_client.py               # Jira REST wrapper (list/get incidents, transitions, comments)
│   ├── git_manager.py               # Git operations: clone/pull, branch, write, commit, push
│   └── pr_manager.py                # GitHub PR creation to master, stage, integration
└── slack_bot/
    ├── app.py                       # Slack Bolt app — registers /list-open-incidents, /resolve-incident
    └── mcp_client.py                # Async MCP SSE client used by the Slack bot
```

## Key Design Decisions

- **MCP-first**: Always prefer MCP integrations over direct REST API calls to Slack, Jira, and GitHub
- **Python only**: All server-side code, integrations, and tooling must be in Python
- **Multi-branch PRs**: Every fix must produce PRs targeting `master`, `stage`, and `integration`
- **Local LLM**: The LLM runs on a dedicated server and is called via MCP, not via cloud API directly
