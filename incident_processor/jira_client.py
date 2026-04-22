from jira import JIRA
import config


class JiraClient:
    def __init__(self):
        self._client = JIRA(
            server=config.JIRA_SERVER,
            basic_auth=(config.JIRA_EMAIL, config.JIRA_API_TOKEN),
        )

    def get_open_incidents(self) -> list[dict]:
        jql = f'project = "{config.JIRA_PROJECT_KEY}" AND status = "TODO" ORDER BY created DESC'
        issues = self._client.search_issues(jql, maxResults=50)
        return [
            {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description or "",
                "priority": str(issue.fields.priority),
                "created": str(issue.fields.created),
            }
            for issue in issues
        ]

    def get_incident(self, incident_id: str) -> dict:
        issue = self._client.issue(incident_id)
        return {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": issue.fields.description or "",
            "priority": str(issue.fields.priority),
            "status": str(issue.fields.status),
            "reporter": str(issue.fields.reporter),
            "created": str(issue.fields.created),
            "labels": list(issue.fields.labels),
            "components": [c.name for c in issue.fields.components],
        }

    def transition_incident(self, incident_id: str, status: str) -> None:
        transitions = self._client.transitions(incident_id)
        target = next((t for t in transitions if t["name"].lower() == status.lower()), None)
        if target:
            self._client.transition_issue(incident_id, target["id"])

    def add_comment(self, incident_id: str, comment: str) -> None:
        self._client.add_comment(incident_id, comment)
