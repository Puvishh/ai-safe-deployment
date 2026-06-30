from fastapi import APIRouter, HTTPException

from app.collectors.git.collector import GitCollector
from app.collectors.git.parser import GitParser
from app.collectors.git.classifier import GitFileClassifier

from app.services.context_builder import DeploymentContextBuilder
from app.risk.risk_engine import RiskEngine

from app.schemes.git import (
    GitAnalyzeRequest,
    GitAnalyzeResponse,
    RepositoryInfo,
    ChangedFile,
)

router = APIRouter(
    prefix="/git",
    tags=["Git Collector"]
)


@router.post("/analyze")
def analyze_repository(request: GitAnalyzeRequest):
    try:
        # Step 1: Collect repository information
        collector = GitCollector(request.repository_path)

        # Step 2: Parse changed files
        parser = GitParser(collector.repo)

        # Step 3: Classify files
        classifier = GitFileClassifier()

        changed_files = []

        for file in parser.get_changed_files():
            changed_files.append(
                ChangedFile(
                    path=file["path"],
                    status=file["status"],
                    category=classifier.classify(file["path"]),
                )
            )

        # Step 4: Repository information
        repository = RepositoryInfo(
            name=collector.get_repository_name(),
            branch=collector.get_current_branch(),
            latest_commit=collector.get_latest_commit_hash(),
            author=collector.get_latest_commit_author(),
            latest_commit_message=collector.get_latest_commit_message(),
        )

        # Step 5: Build Git Response
        git_response = GitAnalyzeResponse(
            success=True,
            repository=repository,
            changes=changed_files,
        )

        # Step 6: Build Deployment Context
        context_builder = DeploymentContextBuilder()
        deployment_context = context_builder.build(git_response)

        # Step 7: Calculate Risk
        risk_engine = RiskEngine()
        risk_result = risk_engine.calculate_risk(deployment_context)

        # Step 8: Final Response
        return {
            "git_analysis": git_response.model_dump(),  # Use .dict() if using Pydantic V1
            "deployment_context": deployment_context,
            "risk_analysis": risk_result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )