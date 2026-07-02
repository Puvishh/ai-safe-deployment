"""
AI Explanation Engine
=====================
Converts structured deployment findings into human-readable explanations
and a deterministic deployment decision using template-based reasoning.

No external LLM APIs are used. All output is produced deterministically
from the structured input data.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Decision thresholds
# ---------------------------------------------------------------------------

_APPROVE_MAX_SCORE: int = 39   # overall_score <= 39  → APPROVE
_REVIEW_MAX_SCORE: int = 74    # overall_score <= 74  → REVIEW
                                # overall_score >= 75  → REJECT

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

_SUMMARY_TEMPLATES: dict[str, str] = {
    "LOW": (
        "This deployment carries a low risk profile. "
        "The changes are contained and no critical issues were detected. "
        "Standard deployment procedures apply."
    ),
    "MEDIUM": (
        "This deployment carries a moderate risk profile. "
        "Several findings require attention before proceeding. "
        "A careful review and targeted mitigations are recommended."
    ),
    "HIGH": (
        "This deployment carries a high risk profile. "
        "Critical findings have been detected that could destabilise the production environment. "
        "Deployment should be halted until all blocking issues are resolved."
    ),
}

_DECISION_RATIONALE: dict[str, str] = {
    "APPROVE": (
        "All analysis engines report acceptable risk levels. "
        "No blocking findings are present. The deployment may proceed."
    ),
    "REVIEW": (
        "One or more analysis engines have flagged concerns that exceed acceptable thresholds. "
        "The deployment should be reviewed by a senior engineer before proceeding."
    ),
    "REJECT": (
        "Critical risk levels have been detected across one or more analysis domains. "
        "The deployment must not proceed until all critical findings are remediated and re-evaluated."
    ),
}

_BUSINESS_IMPACT_TEMPLATES: dict[str, str] = {
    "LOW": (
        "Minimal business impact is anticipated. "
        "The probability of service degradation is low and any issues are expected to be self-contained."
    ),
    "MEDIUM": (
        "Moderate business impact is possible. "
        "There is an elevated probability of partial service degradation or increased error rates "
        "if unaddressed findings are carried into production."
    ),
    "HIGH": (
        "Significant business impact is likely. "
        "Proceeding with this deployment risks service outages, data inconsistency, "
        "or cascading failures that may affect end-users and downstream systems."
    ),
}


# ---------------------------------------------------------------------------
# Helper components (Open/Closed principle — extend by adding new helpers)
# ---------------------------------------------------------------------------

class _DecisionResolver:
    """Resolves a deployment decision from a numeric risk score."""

    def resolve(self, score: int) -> str:
        """
        Determines the deployment decision based on the overall risk score.

        Args:
            score: Numeric risk score in the range 0–100.

        Returns:
            One of "APPROVE", "REVIEW", or "REJECT".
        """
        if score <= _APPROVE_MAX_SCORE:
            return "APPROVE"
        if score <= _REVIEW_MAX_SCORE:
            return "REVIEW"
        return "REJECT"


class _DetailedExplanationBuilder:
    """Builds the detailed explanation section from findings and recommendations."""

    def build(
        self,
        level: str,
        score: int,
        findings: list[Any],
        recommendations: list[str],
        decision: str,
    ) -> str:
        """
        Constructs a multi-paragraph, professional explanation string.

        Args:
            level: Risk level string — "LOW", "MEDIUM", or "HIGH".
            score: Overall numeric risk score.
            findings: List of finding objects or dicts from upstream engines.
            recommendations: Deduplicated list of recommendation strings.
            decision: Resolved deployment decision ("APPROVE" | "REVIEW" | "REJECT").

        Returns:
            A formatted multi-paragraph explanation string.
        """
        paragraphs: list[str] = []

        # Paragraph 1 — risk overview
        paragraphs.append(
            f"The deployment analysis produced an overall risk score of {score} "
            f"({level}). "
            + _DECISION_RATIONALE[decision]
        )

        # Paragraph 2 — findings summary
        finding_count = len(findings)
        if finding_count == 0:
            paragraphs.append("No individual findings were reported by the analysis engines.")
        elif finding_count == 1:
            paragraphs.append(
                "One finding was identified during analysis. "
                "Please review the recommendations section for remediation guidance."
            )
        else:
            paragraphs.append(
                f"{finding_count} findings were identified during analysis. "
                "Each finding has been evaluated for severity and business impact. "
                "Please review the recommendations section for prioritised remediation guidance."
            )

        # Paragraph 3 — recommendations overview
        rec_count = len(recommendations)
        if rec_count == 0:
            paragraphs.append("No specific remediation actions are required at this time.")
        else:
            paragraphs.append(
                f"{rec_count} remediation action(s) have been identified. "
                "Addressing all recommendations before deployment will reduce residual risk."
            )

        return "\n\n".join(paragraphs)


class _RecommendedActionsBuilder:
    """Produces a prioritised, de-duplicated list of recommended actions."""

    def build(self, recommendations: list[str], decision: str) -> list[str]:
        """
        Returns the recommended actions, prefixed with a decision-specific action
        if the deployment is not being approved.

        Args:
            recommendations: Existing recommendation strings from upstream engines.
            decision: Resolved deployment decision.

        Returns:
            A list of action strings, with a leading decision-specific action where
            appropriate.
        """
        actions: list[str] = list(dict.fromkeys(recommendations))  # preserve order, deduplicate

        if decision == "REJECT":
            actions.insert(
                0,
                "BLOCK deployment immediately and notify the engineering team for urgent review.",
            )
        elif decision == "REVIEW":
            actions.insert(
                0,
                "SCHEDULE a senior engineer review before proceeding with this deployment.",
            )

        return actions


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------

class ExplanationEngine:
    """
    Converts structured deployment analysis findings into a human-readable
    deployment explanation and decision using deterministic template-based reasoning.

    This engine does not call any external services or LLM APIs. All output
    is produced deterministically from the structured input data.

    Follows the Single Responsibility Principle: this class orchestrates the
    explanation pipeline; each transformation step is delegated to a focused
    helper component.
    """

    def __init__(self) -> None:
        self._decision_resolver = _DecisionResolver()
        self._explanation_builder = _DetailedExplanationBuilder()
        self._actions_builder = _RecommendedActionsBuilder()

    def explain(
        self,
        overall_risk: dict[str, Any],
        findings: list[Any],
        recommendations: list[str],
    ) -> dict[str, Any]:
        """
        Produces a structured, human-readable deployment explanation.

        Args:
            overall_risk: Output from OverallRiskEngine.calculate(), containing at
                          minimum ``overall_score`` (int) and ``overall_level`` (str).
            findings: List of finding objects/dicts surfaced by upstream analysis engines.
            recommendations: Deduplicated list of recommendation strings.

        Returns:
            A dict with the following keys:
                - ``summary`` (str): One-paragraph executive summary.
                - ``detailed_explanation`` (str): Multi-paragraph technical explanation.
                - ``deployment_decision`` (str): "APPROVE", "REVIEW", or "REJECT".
                - ``business_impact`` (str): Assessment of potential business impact.
                - ``recommended_actions`` (list[str]): Prioritised list of actions.
        """
        logger.info("ExplanationEngine.explain() invoked.")

        score: int = int(overall_risk.get("overall_score", 0))
        level: str = overall_risk.get("overall_level", "LOW").upper()

        # Guard against unexpected level values
        if level not in _SUMMARY_TEMPLATES:
            logger.warning(
                "Unrecognised risk level '%s'; defaulting to 'HIGH' for safety.", level
            )
            level = "HIGH"

        decision: str = self._decision_resolver.resolve(score)
        logger.info("Deployment decision resolved to '%s' for score=%d.", decision, score)

        summary: str = _SUMMARY_TEMPLATES[level]
        business_impact: str = _BUSINESS_IMPACT_TEMPLATES[level]

        detailed_explanation: str = self._explanation_builder.build(
            level=level,
            score=score,
            findings=findings,
            recommendations=recommendations,
            decision=decision,
        )

        recommended_actions: list[str] = self._actions_builder.build(
            recommendations=recommendations,
            decision=decision,
        )

        result: dict[str, Any] = {
            "summary": summary,
            "detailed_explanation": detailed_explanation,
            "deployment_decision": decision,
            "business_impact": business_impact,
            "recommended_actions": recommended_actions,
        }

        logger.info("ExplanationEngine produced decision='%s'.", decision)
        return result
