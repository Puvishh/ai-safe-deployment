"""
Git Diff Analyzer

Analyzes the actual content changes between Git versions.
"""

from git import Repo


class GitDiffAnalyzer:
    """
    Analyzes Git diffs for changed files.
    """

    def __init__(self, repo: Repo):
        self.repo = repo

    def get_file_diff(self, file_path: str) -> str:
        """
        Returns the textual diff of a file.
        """

        try:
            diff = self.repo.git.diff("HEAD", file_path)
            return diff
        except Exception:
            return ""

    def analyze(self, changed_files: list) -> list:
        """
        Analyze all changed files and attach their diff.
        """

        results = []

        for file in changed_files:
            results.append(
                {
                    "path": file["path"],
                    "status": file["status"],
                    "diff": self.get_file_diff(file["path"]),
                }
            )

        return results