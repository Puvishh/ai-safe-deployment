from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.collectors.git.collector import GitCollector
from app.collectors.git.parser import GitParser
from app.collectors.git.classifier import GitFileClassifier

from app.collectors.kubernetes.analyzer import KubernetesAnalyzer

from app.services.context_builder import DeploymentContextBuilder
from app.risk.risk_engine import RiskEngine
from app.risk.overall_risk_engine import OverallRiskEngine
from app.ai.explanation_engine import ExplanationEngine

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

        # ---------------------------------------
        # Git Collection
        # ---------------------------------------

        collector = GitCollector(request.repository_path)

        parser = GitParser(collector.repo)

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

        repository = RepositoryInfo(
            name=collector.get_repository_name(),
            branch=collector.get_current_branch(),
            latest_commit=collector.get_latest_commit_hash(),
            author=collector.get_latest_commit_author(),
            latest_commit_message=collector.get_latest_commit_message(),
        )

        git_response = GitAnalyzeResponse(
            success=True,
            repository=repository,
            changes=changed_files,
        )

        # ---------------------------------------
        # Deployment Context
        # ---------------------------------------

        context_builder = DeploymentContextBuilder()

        deployment_context = context_builder.build(git_response)

        # ---------------------------------------
        # Git Risk
        # ---------------------------------------

        risk_engine = RiskEngine()

        git_risk = risk_engine.calculate_risk(
            deployment_context
        )

        # ---------------------------------------
        # Kubernetes Analysis
        # ---------------------------------------

        kubernetes_analysis = None

        try:

            analyzer = KubernetesAnalyzer()

            repo_path = Path(request.repository_path)

            old_yaml = repo_path / deployment_context["kubernetes"]["old_yaml"]

            new_yaml = repo_path / deployment_context["kubernetes"]["new_yaml"]

            kubernetes_analysis = analyzer.analyze(
                str(old_yaml),
                str(new_yaml),
            )

        except Exception as e:

            kubernetes_analysis = {
                "error": str(e)
            }

        # ---------------------------------------
        # Overall Risk
        # ---------------------------------------

        overall_risk_engine = OverallRiskEngine()

        overall_risk = overall_risk_engine.calculate(
            git_risk=git_risk,
            kubernetes_analysis=kubernetes_analysis if isinstance(kubernetes_analysis, dict) else {},
        )
        explanation_engine = ExplanationEngine()

        ai_explanation = explanation_engine.explain(
            overall_risk=overall_risk,
            findings=kubernetes_analysis["findings"],
            recommendations=kubernetes_analysis["recommendations"],
)

        # ---------------------------------------
        # Final Response
        # ---------------------------------------

        return {
            "git_analysis": git_response.model_dump(),
            "deployment_context": deployment_context,
            "git_risk": git_risk,
            "kubernetes_analysis": kubernetes_analysis,
            "overall_risk": overall_risk,
            "ai_explanation": ai_explanation,
        }

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )