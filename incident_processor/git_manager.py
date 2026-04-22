import os
import subprocess
from pathlib import Path
import git
import config


class GitManager:
    def __init__(self):
        self.repos_dir = Path(config.REPOS_DIR)
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    def repo_path(self, repo_name: str) -> Path:
        return self.repos_dir / repo_name

    def clone_or_pull(self, repo_url: str, repo_name: str) -> Path:
        path = self.repo_path(repo_name)
        if path.exists():
            repo = git.Repo(path)
            repo.remotes.origin.pull()
        else:
            git.Repo.clone_from(repo_url, path)
        return path

    def create_branch(self, repo_path: Path, branch_name: str) -> None:
        repo = git.Repo(repo_path)
        if branch_name in repo.heads:
            repo.heads[branch_name].checkout()
        else:
            repo.create_head(branch_name).checkout()

    def commit_and_push(self, repo_path: Path, message: str, branch: str) -> None:
        repo = git.Repo(repo_path)
        repo.git.add(A=True)
        if repo.is_dirty(index=True):
            repo.index.commit(message)
        repo.remotes.origin.push(refspec=f"{branch}:{branch}")

    def list_files(self, repo_path: Path, pattern: str = "**/*") -> list[str]:
        return [
            str(p.relative_to(repo_path))
            for p in repo_path.glob(pattern)
            if p.is_file() and ".git" not in p.parts
        ]

    def read_file(self, repo_path: Path, relative_path: str) -> str:
        return (repo_path / relative_path).read_text(encoding="utf-8")

    def write_file(self, repo_path: Path, relative_path: str, content: str) -> None:
        target = repo_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def run_command(self, repo_path: Path, command: str) -> str:
        result = subprocess.run(
            command,
            shell=True,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout
        if result.returncode != 0:
            output += f"\nSTDERR: {result.stderr}"
        return output
