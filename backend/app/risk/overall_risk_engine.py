"""
Overall Risk Engine

Combines multiple analysis engines (Git, Kubernetes, etc.)
into a single deployment risk assessment.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class OverallRiskEngine:
    """
    Combines the outputs of multiple analysis engines into
    a single deployment risk assessment.

    Responsibilities:
    - Aggregate risk scores
    - Determine overall risk level
    - Merge recommendations
    - Generate deployment summary
    """

    def calculate(
        self,
        git_risk: Dict[str, Any],
        kubernetes_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate the overall deployment risk.

        Args:
            git_risk:
                Expected keys:
                - risk_score
                - recommendations

            kubernetes_analysis:
                Expected keys:
                - risk_score
                - recommendations

        Returns:
            Dictionary containing:
            - overall_score
            - overall_level
            - summary
            - recommendations
        """

        logger.info("Calculating overall deployment risk...")

        git_score = int(git_risk.get("risk_score", 0))
        k8s_score = int(kubernetes_analysis.get("risk_score", 0))

        overall_score = self._calculate_combined_score(
            git_score,
            k8s_score,
        )

        overall_level = self._determine_risk_level(
            overall_score
        )

        recommendations = self._deduplicate_recommendations(
            git_risk.get("recommendations", []),
            kubernetes_analysis.get("recommendations", []),
        )

        summary = self._generate_summary(
            overall_level,
            git_score,
            k8s_score,
            overall_score,
        )

        result = {
            "overall_score": overall_score,
            "overall_level": overall_level,
            "summary": summary,
            "recommendations": recommendations,
        }

        logger.info(
            "Overall deployment risk calculated successfully."
        )

        return result

    def _calculate_combined_score(
        self,
        git_score: int,
        k8s_score: int,
    ) -> int:
        """
        Calculate the overall deployment score.

        Strategy:
        The deployment inherits the highest risk reported by any
        analysis engine.

        This prevents a critical Kubernetes risk from being hidden
        by a low Git risk.

        Future versions can include:
        - Docker analysis
        - Terraform analysis
        - Helm analysis
        """

        return max(git_score, k8s_score)

    def _determine_risk_level(
        self,
        score: int,
    ) -> str:
        """
        Convert numeric score into a deployment risk level.
        """

        if score >= 75:
            return "HIGH"

        if score >= 40:
            return "MEDIUM"

        return "LOW"

    def _deduplicate_recommendations(
        self,
        *recommendation_lists: List[str],
    ) -> List[str]:
        """
        Merge recommendation lists while preserving order
        and removing duplicates.
        """

        unique_recommendations: List[str] = []
        seen = set()

        for recommendation_list in recommendation_lists:

            for recommendation in recommendation_list:

                if recommendation not in seen:
                    seen.add(recommendation)
                    unique_recommendations.append(recommendation)

        return unique_recommendations

    def _generate_summary(
        self,
        level: str,
        git_score: int,
        k8s_score: int,
        overall_score: int,
    ) -> str:
        """
        Generate a human-readable deployment summary.
        """

        return (
            f"Overall deployment risk is {level} "
            f"(Score: {overall_score}). "
            f"Contributing scores - "
            f"Git Analysis: {git_score}, "
            f"Kubernetes Analysis: {k8s_score}."
        )