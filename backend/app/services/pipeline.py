"""
Deployment Analysis Pipeline

Connects all modules together.
"""

from app.collectors.git.collector import GitCollector
from app.collectors.git.parser import GitParser
from app.collectors.git.classifier import GitFileClassifier
from app.collectors.git.diff_analyzer import GitDiffAnalyzer
from app.collectors.git.change_detector import DeploymentChangeDetector
from app.services.context_builder import DeploymentContextBuilder
from app.risk.risk_engine import RiskEngine
from app.schemes.git import (
    ChangedFile,
    GitAnalyzeResponse,
    RepositoryInfo,
)


class DeploymentPipeline:

    def analyze(self, repository_path: str):

        # Step 1
        collector = GitCollector(repository_path)

        # Step 2
        parser = GitParser(collector.repo)

        raw_files = parser.get_changed_files()

        # Step 3
        classifier = GitFileClassifier()

        changed_files = []

        for file in raw_files:
            changed_files.append(
                ChangedFile(
                    path=file["path"],
                    status=file["status"],
                    category=classifier.classify(file["path"])
                )
            )

        # Step 4
        git_response = GitAnalyzeResponse(
            success=True,
            repository=RepositoryInfo(
                name=collector.get_repository_name(),
                branch=collector.get_current_branch(),
                latest_commit=collector.get_latest_commit_hash(),
                author=collector.get_latest_commit_author(),
                latest_commit_message=collector.get_latest_commit_message()
            ),
            changes=changed_files
        )

        # Step 5
        context = DeploymentContextBuilder().build(git_response)

        # Step 6
        risk = RiskEngine().calculate_risk(context)

        return {
            "git": git_response.model_dump(),
            "context": context,
            "risk": risk
        }