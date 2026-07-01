"""
Deployment Risk Rules

This module contains all deployment risk evaluation rules.
"""

from typing import List, Dict


class DeploymentRiskRules:
    """
    Contains deployment risk evaluation rules.
    """

    def evaluate(self, detected_changes: List[Dict]) -> Dict:

        score = 0
        reasons = []

        for change in detected_changes:

            field = change["field"]

            if field == "replicas":
                score += 30
                reasons.append(
                    "Replica count changed. This may affect application availability."
                )

            elif field == "image":
                score += 25
                reasons.append(
                    "Container image changed. Verify image tag and compatibility."
                )

            elif field == "memory":
                score += 20
                reasons.append(
                    "Memory configuration changed."
                )

            elif field == "cpu":
                score += 15
                reasons.append(
                    "CPU allocation changed."
                )

            elif field == "environment":
                score += 15
                reasons.append(
                    "Environment variables changed."
                )

        if score >= 60:
            level = "HIGH"
        elif score >= 30:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "risk_score": score,
            "risk_level": level,
            "reasons": reasons,
        }