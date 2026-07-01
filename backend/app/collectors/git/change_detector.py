"""
Deployment Change Detector

Converts raw Git diffs into structured deployment changes.
"""

from typing import List, Dict


class DeploymentChangeDetector:
    """
    Detects deployment-related changes from Git diffs.
    """

    def detect_changes(self, analyzed_files: List[Dict]) -> List[Dict]:

        detected_changes = []

        for file in analyzed_files:

            diff = file.get("diff", "")

            path = file.get("path", "")

            # Replica Changes
            if "replicas:" in diff:
                detected_changes.append(
                    {
                        "resource": path,
                        "field": "replicas",
                        "change_type": "deployment",
                        "severity": "HIGH"
                    }
                )

            # Memory Changes
            if "memory:" in diff:
                detected_changes.append(
                    {
                        "resource": path,
                        "field": "memory",
                        "change_type": "resource",
                        "severity": "HIGH"
                    }
                )

            # CPU Changes
            if "cpu:" in diff:
                detected_changes.append(
                    {
                        "resource": path,
                        "field": "cpu",
                        "change_type": "resource",
                        "severity": "MEDIUM"
                    }
                )

            # Docker Image Changes
            if "image:" in diff:
                detected_changes.append(
                    {
                        "resource": path,
                        "field": "image",
                        "change_type": "deployment",
                        "severity": "HIGH"
                    }
                )

            # Environment Variable Changes
            if "env:" in diff:
                detected_changes.append(
                    {
                        "resource": path,
                        "field": "environment",
                        "change_type": "configuration",
                        "severity": "MEDIUM"
                    }
                )

        return detected_changes