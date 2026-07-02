import logging
from typing import Any, Dict, List

from .yaml_reader import KubernetesYAMLReader
from .detectors.replica_detector import ReplicaDetector
from .detectors.image_detector import ImageDetector
from .detectors.memory_detector import MemoryDetector
from .detectors.cpu_detector import CPUDetector
from .detectors.probe_detector import ProbeDetector
from .detectors.env_detector import EnvDetector

logger = logging.getLogger(__name__)


class KubernetesAnalyzer:
    """
    Analyze two Kubernetes Deployment YAML files and generate
    deployment risk analysis.
    """

    HIGH_SCORE = 30
    MEDIUM_SCORE = 15
    LOW_SCORE = 5

    def __init__(self):
        self.yaml_reader = KubernetesYAMLReader()

        self.detectors = (
            ReplicaDetector(),
            ImageDetector(),
            MemoryDetector(),
            CPUDetector(),
            ProbeDetector(),
            EnvDetector(),
        )

    def _calculate_risk(self, findings: List[Dict[str, Any]]) -> tuple[int, str]:
        """
        Calculate overall deployment risk.
        """

        score = 0

        for finding in findings:

            severity = finding.get("severity", "NONE").upper()

            if severity == "HIGH":
                score += self.HIGH_SCORE

            elif severity == "MEDIUM":
                score += self.MEDIUM_SCORE

            elif severity == "LOW":
                score += self.LOW_SCORE

        if score > 50:
            level = "HIGH"

        elif score >= 21:
            level = "MEDIUM"

        else:
            level = "LOW"

        return score, level

    def analyze(
        self,
        old_yaml_path: str,
        new_yaml_path: str
    ) -> Dict[str, Any]:
        """
        Run every Kubernetes detector and aggregate the results.
        """

        logger.info("Starting Kubernetes deployment analysis...")

        try:

            old_yaml = self.yaml_reader.read_yaml(old_yaml_path)
            new_yaml = self.yaml_reader.read_yaml(new_yaml_path)

        except Exception as e:
            logger.exception(e)
            raise ValueError(f"Unable to load YAML files: {e}")

        if isinstance(old_yaml, list):
            old_yaml = old_yaml[0]

        if isinstance(new_yaml, list):
            new_yaml = new_yaml[0]

        findings: List[Dict[str, Any]] = []
        recommendations: List[str] = []

        for detector in self.detectors:

            try:

                result = detector.detect(old_yaml, new_yaml)

                if not isinstance(result, dict):
                    continue

                if result.get("changed", False):
                    findings.append(result)

                recommendation = result.get("recommendation")

                if recommendation:

                    if isinstance(recommendation, list):

                        for rec in recommendation:
                            if rec not in recommendations:
                                recommendations.append(rec)

                    else:

                        if recommendation not in recommendations:
                            recommendations.append(recommendation)

            except Exception as e:

                logger.exception(
                    f"{detector.__class__.__name__} failed: {e}"
                )

        risk_score, risk_level = self._calculate_risk(findings)

        logger.info(
            f"Analysis completed. Risk Score={risk_score}, Level={risk_level}"
        )

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "total_findings": len(findings),
            "analyzed_detectors": len(self.detectors),
            "findings": findings,
            "recommendations": recommendations,
        }