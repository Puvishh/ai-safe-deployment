"""
Git Parser

This module is responsible for parsing changed files from a Git repository.
It extracts raw change information while ignoring generated/system files.
"""

from pathlib import Path

from git import Repo


class GitParser:
    """
    Parses changed files from a Git repository.
    """

    # Directories to ignore
    IGNORE_DIRECTORIES = {
        "__pycache__",
        ".git",
        ".venv",
        ".idea",
        ".vscode",
        "node_modules",
    }

    # File extensions to ignore
    IGNORE_EXTENSIONS = {
        ".pyc",
        ".pyo",
    }

    # Specific files to ignore
    IGNORE_FILES = {
        ".DS_Store",
    }

    def __init__(self, repo: Repo):
        self.repo = repo

    def _should_ignore(self, file_path: str) -> bool:
        """
        Returns True if the file should be ignored.
        """

        path = Path(file_path)

        # Ignore directories
        for part in path.parts:
            if part in self.IGNORE_DIRECTORIES:
                return True

        # Ignore file extensions
        if path.suffix in self.IGNORE_EXTENSIONS:
            return True

        # Ignore specific filenames
        if path.name in self.IGNORE_FILES:
            return True

        return False

    def get_changed_files(self) -> list[dict]:
        """
        Returns a list of changed files.

        Example:
        [
            {
                "path": "k8s/deployment.yaml",
                "status": "modified"
            }
        ]
        """

        changed_files = []

        # Modified files
        for item in self.repo.index.diff(None):

            if self._should_ignore(item.a_path):
                continue

            changed_files.append(
                {
                    "path": item.a_path,
                    "status": "modified",
                }
            )

        # Untracked files
        for file in self.repo.untracked_files:

            if self._should_ignore(file):
                continue

            changed_files.append(
                {
                    "path": file,
                    "status": "untracked",
                }
            )

        return changed_files