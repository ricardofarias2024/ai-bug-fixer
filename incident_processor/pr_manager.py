from github import Github, GithubException
import config

TARGET_BRANCHES = ["master", "stage", "integration"]


class PRManager:
    def __init__(self):
        self._gh = Github(config.GITHUB_TOKEN)

    def _get_repo(self, repo_name: str):
        full_name = f"{config.GITHUB_ORG}/{repo_name}" if config.GITHUB_ORG else repo_name
        return self._gh.get_repo(full_name)

    def create_prs(
        self,
        repo_name: str,
        head_branch: str,
        title: str,
        body: str,
    ) -> list[dict]:
        repo = self._get_repo(repo_name)
        results = []

        for base in TARGET_BRANCHES:
            try:
                pr = repo.create_pull(
                    title=title,
                    body=body,
                    head=head_branch,
                    base=base,
                )
                results.append({"base": base, "url": pr.html_url, "number": pr.number})
            except GithubException as e:
                results.append({"base": base, "error": str(e)})

        return results
