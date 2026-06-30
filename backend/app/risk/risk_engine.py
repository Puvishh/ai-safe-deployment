"""
Risk Intelligence Engine

Calculates deployment risk based on deployment context.
"""

class RiskEngine:

    def calculate_risk(self, deployment_context: dict) -> dict:

        score = 0
        reasons = []

        # Kubernetes deployment files
        if deployment_context["deployment_files"]:
            score += 25
            reasons.append("Kubernetes deployment configuration changed.")

        # Docker changes
        if deployment_context["docker_files"]:
            score += 15
            reasons.append("Docker image/build configuration changed.")

        # Configuration changes
        if deployment_context["config_files"]:
            score += 20
            reasons.append("Application configuration changed.")

        # Large source code changes
        if len(deployment_context["source_files"]) > 10:
            score += 20
            reasons.append("Large source code change detected.")

        # Determine risk level
        if score >= 60:
            level = "HIGH"
        elif score >= 30:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "risk_score": score,
            "risk_level": level,
            "reasons": reasons
        }