"""
Git Collector

This module is responsible for collecting information from a local Git
repository. It does NOT parse or classify files. It only collects raw
repository information.

Author: AI Safe Deployment
"""

from pathlib import Path
from git import Repo, InvalidGitRepositoryError, NoSuchPathError


class GitCollector:
    """
    Collects basic information from a Git repository.
    """

    def __init__(self, repository_path: str):
        """
        Initialize the Git Collector.

        Args:
            repository_path (str): Path to the local Git repository.
        """
        self.repository_path = Path(repository_path)

        if not self.repository_path.exists():
            raise FileNotFoundError(
                f"Repository path does not exist: {repository_path}"
            )

        try:
            self.repo = Repo(self.repository_path)
        except InvalidGitRepositoryError:
            raise ValueError(
                f"{repository_path} is not a valid Git repository."
            )
        except NoSuchPathError:
            raise FileNotFoundError(
                f"Repository path not found: {repository_path}"
            )

    def get_repository_name(self) -> str:
        """
        Returns the repository name.
        """
        return self.repository_path.name

    def get_current_branch(self) -> str:
        """
        Returns the currently checked-out branch.
        """
        return self.repo.active_branch.name

    def get_latest_commit_hash(self) -> str:
        """
        Returns the latest commit hash.
        """
        return self.repo.head.commit.hexsha

    def get_latest_commit_author(self) -> str:
        """
        Returns the latest commit author.
        """
        return self.repo.head.commit.author.name

    def get_latest_commit_message(self) -> str:
        """
        Returns the latest commit message.
        """
        return self.repo.head.commit.message.strip()

    def collect_repository_info(self) -> dict:
        """
        Collect all repository information.

        Returns:
            dict: Repository metadata.
        """
        return {
            "name": self.get_repository_name(),
            "branch": self.get_current_branch(),
            "latest_commit": self.get_latest_commit_hash(),
            "author": self.get_latest_commit_author(),
            "latest_commit_message": self.get_latest_commit_message(),
        }