"""
Git Parser

This module is responsible for parsing changed files from a Git repository.
It does NOT classify files. It only extracts raw change information.
"""

from git import Repo


class GitParser:
    """
    Parses changed files from a Git repository.
    """

    def __init__(self, repo: Repo):
        self.repo = repo

    def get_changed_files(self) -> list[dict]:
        """
        Returns a list of changed files.

        Output Example:
        [
            {
                "path": "Dockerfile",
                "status": "modified"
            },
            {
                "path": "k8s/deployment.yaml",
                "status": "modified"
            }
        ]
        """

        changed_files = []

        # Modified files
        for item in self.repo.index.diff(None):
            changed_files.append(
                {
                    "path": item.a_path,
                    "status": "modified"
                }
            )

        # Untracked files
        for file in self.repo.untracked_files:
            changed_files.append(
                {
                    "path": file,
                    "status": "untracked"
                }
            )

        return changed_files