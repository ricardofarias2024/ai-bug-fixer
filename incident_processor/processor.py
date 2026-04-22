import json
import re
from pathlib import Path

import anthropic

import config
from incident_processor.git_manager import GitManager
from incident_processor.jira_client import JiraClient
from incident_processor.pr_manager import PRManager

TOOLS = [
    {
        "name": "list_files",
        "description": "List files in the cloned repository, optionally filtered by glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern, e.g. '**/*.py'. Defaults to '**/*'.",
                }
            },
        },
    },
    {
        "name": "read_file",
        "description": "Read the content of a file in the repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path inside the repository."}
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write or overwrite a file in the repository with new content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path inside the repository."},
                "content": {"type": "string", "description": "Full file content to write."},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "run_command",
        "description": "Run a shell command inside the repository directory (tests, linters, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute."}
            },
            "required": ["command"],
        },
    },
    {
        "name": "create_pull_requests",
        "description": "Commit all changes, push the fix branch, and open PRs to master, stage, and integration.",
        "input_schema": {
            "type": "object",
            "properties": {
                "commit_message": {"type": "string"},
                "pr_title": {"type": "string"},
                "pr_body": {"type": "string"},
            },
            "required": ["commit_message", "pr_title", "pr_body"],
        },
    },
]

SYSTEM_PROMPT = """You are an expert software engineer. Your task is to analyze a bug report from Jira and fix it in the codebase.

Steps you must follow:
1. Read the incident description carefully to understand the bug.
2. Explore the repository structure with list_files and read_file to locate the relevant code.
3. Identify the root cause and apply a minimal, correct fix using write_file.
4. Validate the fix with run_command (run tests or linters if available).
5. Call create_pull_requests to commit and open PRs to master, stage, and integration.

Important rules:
- Fix only what is necessary. Do not refactor unrelated code.
- Always run available tests after making changes.
- The PR body must include: root cause, fix description, and testing done.
"""


class IncidentProcessor:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self._jira = JiraClient()
        self._git = GitManager()
        self._pr = PRManager()
        self._repo_path: Path | None = None
        self._repo_name: str | None = None

    async def process(self, incident_id: str) -> str:
        incident = self._jira.get_incident(incident_id)
        self._jira.transition_incident(incident_id, "In Progress")

        repo_name, repo_url = self._detect_repo(incident)
        self._repo_name = repo_name
        self._repo_path = self._git.clone_or_pull(repo_url, repo_name)

        fix_branch = f"fix/{incident_id.lower()}"
        self._git.create_branch(self._repo_path, fix_branch)
        self._fix_branch = fix_branch

        user_message = (
            f"Incident ID: {incident['key']}\n"
            f"Summary: {incident['summary']}\n\n"
            f"Description:\n{incident['description']}\n\n"
            f"Repository: {repo_name}\n"
            "Please analyze, fix the bug, and create the pull requests."
        )

        messages = [{"role": "user", "content": user_message}]
        result_summary = await self._run_agent_loop(messages, incident_id)

        self._jira.add_comment(incident_id, f"Fix applied by AI Bug Fixer.\n\n{result_summary}")
        self._jira.transition_incident(incident_id, "Done")

        return result_summary

    async def _run_agent_loop(self, messages: list, incident_id: str) -> str:
        while True:
            response = self._client.messages.create(
                model=config.ANTHROPIC_MODEL,
                max_tokens=8096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                text_blocks = [b.text for b in response.content if hasattr(b, "text")]
                return "\n".join(text_blocks) or "Fix completed."

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                output = self._execute_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(output),
                    }
                )

            messages.append({"role": "user", "content": tool_results})

    def _execute_tool(self, name: str, args: dict) -> str:
        if self._repo_path is None:
            return "Error: repository not initialized."

        if name == "list_files":
            pattern = args.get("pattern", "**/*")
            files = self._git.list_files(self._repo_path, pattern)
            return "\n".join(files[:200])

        if name == "read_file":
            try:
                return self._git.read_file(self._repo_path, args["path"])
            except FileNotFoundError:
                return f"File not found: {args['path']}"

        if name == "write_file":
            self._git.write_file(self._repo_path, args["path"], args["content"])
            return f"File written: {args['path']}"

        if name == "run_command":
            return self._git.run_command(self._repo_path, args["command"])

        if name == "create_pull_requests":
            self._git.commit_and_push(self._repo_path, args["commit_message"], self._fix_branch)
            prs = self._pr.create_prs(
                self._repo_name,
                self._fix_branch,
                args["pr_title"],
                args["pr_body"],
            )
            lines = []
            for pr in prs:
                if "url" in pr:
                    lines.append(f"PR to {pr['base']}: {pr['url']}")
                else:
                    lines.append(f"PR to {pr['base']} failed: {pr['error']}")
            return "\n".join(lines)

        return f"Unknown tool: {name}"

    def _detect_repo(self, incident: dict) -> tuple[str, str]:
        text = f"{incident['summary']} {incident['description']} {' '.join(incident['labels'])}"
        match = re.search(r"github\.com[:/][\w-]+/([\w.-]+)", text)
        if match:
            repo_name = match.group(1).removesuffix(".git")
            full = re.search(r"github\.com[:/]([\w-]+/[\w.-]+)", text).group(1).removesuffix(".git")
            return repo_name, f"https://github.com/{full}.git"

        # Fallback: use first label or component as repo name
        name = (incident["labels"] or incident["components"] or ["unknown-repo"])[0]
        org = config.GITHUB_ORG
        return name, f"https://github.com/{org}/{name}.git"
