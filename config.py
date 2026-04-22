import os
from dotenv import load_dotenv

load_dotenv()

# Slack
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

# Jira
JIRA_SERVER = os.environ["JIRA_SERVER"]
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "IN")

# GitHub
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_ORG = os.environ.get("GITHUB_ORG", "")

# Anthropic
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# MCP Server
MCP_SERVER_HOST = os.environ.get("MCP_SERVER_HOST", "localhost")
MCP_SERVER_PORT = int(os.environ.get("MCP_SERVER_PORT", "8080"))

# Git
REPOS_DIR = os.environ.get("REPOS_DIR", "/tmp/ai-bug-fixer-repos")
