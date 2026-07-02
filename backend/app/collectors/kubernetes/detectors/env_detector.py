import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class EnvDetector:
    """
    Detects changes in Kubernetes container environment variables.
    """

    def _extract_env_vars(self, yaml_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """
        Extract environment variables from all containers.

        Returns:
            {
                "container-name": {
                    "ENV_NAME": "value",
                    ...
                }
            }
        """

        env_configs: Dict[str, Dict[str, str]] = {}

        try:
            containers: List[Dict[str, Any]] = (
                yaml_data.get("spec", {})
                .get("template", {})
                .get("spec", {})
                .get("containers", [])
            )

            for container in containers:
                container_name = container.get("name", "unknown")

                env_map: Dict[str, str] = {}

                for env in container.get("env", []):

                    if "name" not in env:
                        continue

                    env_name = env["name"]

                    if "value" in env:
                        env_value = str(env["value"])

                    elif "valueFrom" in env:
                        env_value = json.dumps(
                            env["valueFrom"],
                            sort_keys=True
                        )

                    else:
                        env_value = ""

                    env_map[env_name] = env_value

                env_configs[container_name] = env_map

        except Exception as e:
            logger.error(f"Failed to extract environment variables: {e}")

        return env_configs

    def detect(
        self,
        old_yaml: Dict[str, Any],
        new_yaml: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare environment variables between two Kubernetes Deployment YAMLs.
        """

        try:

            old_envs = self._extract_env_vars(old_yaml)
            new_envs = self._extract_env_vars(new_yaml)

            findings = []

            highest_severity = "NONE"

            severity_rank = {
                "NONE": 0,
                "LOW": 1,
                "MEDIUM": 2,
                "HIGH": 3
            }

            all_containers = set(old_envs.keys()) | set(new_envs.keys())

            for container in all_containers:

                old_container = old_envs.get(container, {})
                new_container = new_envs.get(container, {})

                all_variables = set(old_container.keys()) | set(new_container.keys())

                for variable in all_variables:

                    old_value = old_container.get(variable)
                    new_value = new_container.get(variable)

                    if old_value == new_value:
                        continue

                    if old_value is None:

                        severity = "LOW"

                        reason = (
                            f"Environment variable '{variable}' "
                            f"added to container '{container}'."
                        )

                        recommendation = (
                            "Verify the new environment variable is expected."
                        )

                    elif new_value is None:

                        severity = "HIGH"

                        reason = (
                            f"Environment variable '{variable}' "
                            f"removed from container '{container}'."
                        )

                        recommendation = (
                            "Ensure removing this variable will not break the application."
                        )

                    elif "secretKeyRef" in str(old_value) or "secretKeyRef" in str(new_value):

                        severity = "HIGH"

                        reason = (
                            f"Secret reference changed for '{variable}'."
                        )

                        recommendation = (
                            "Review Secret changes carefully before deployment."
                        )

                    elif "configMapKeyRef" in str(old_value) or "configMapKeyRef" in str(new_value):

                        severity = "MEDIUM"

                        reason = (
                            f"ConfigMap reference changed for '{variable}'."
                        )

                        recommendation = (
                            "Verify ConfigMap changes are correct."
                        )

                    else:

                        severity = "MEDIUM"

                        reason = (
                            f"Environment variable '{variable}' value changed."
                        )

                        recommendation = (
                            "Verify the updated configuration value."
                        )

                    if severity_rank[severity] > severity_rank[highest_severity]:
                        highest_severity = severity

                    findings.append(
                        {
                            "container": container,
                            "variable": variable,
                            "old": old_value,
                            "new": new_value,
                            "severity": severity,
                            "reason": reason,
                            "recommendation": recommendation,
                        }
                    )

            if not findings:

                return {
                    "field": "environment",
                    "changed": False,
                    "severity": "NONE",
                    "old_value": [],
                    "new_value": [],
                    "reason": "No environment variable changes detected.",
                    "recommendation": "",
                    "findings": []
                }

            recommendations = list(
                {
                    item["recommendation"]
                    for item in findings
                }
            )

            reasons = list(
                {
                    item["reason"]
                    for item in findings
                }
            )

            return {
                "field": "environment",
                "changed": True,
                "severity": highest_severity,
                "old_value": [
                    {
                        "container": item["container"],
                        "variable": item["variable"],
                        "value": item["old"],
                    }
                    for item in findings
                ],
                "new_value": [
                    {
                        "container": item["container"],
                        "variable": item["variable"],
                        "value": item["new"],
                    }
                    for item in findings
                ],
                "reason": reasons,
                "recommendation": recommendations,
                "findings": findings,
            }

        except Exception as e:

            logger.exception(e)

            return {
                "field": "environment",
                "changed": False,
                "severity": "NONE",
                "old_value": [],
                "new_value": [],
                "reason": "Failed to analyze environment variables.",
                "recommendation": "Check detector logs.",
                "findings": [],
            }


def detect(
    old_yaml: Dict[str, Any],
    new_yaml: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Module-level helper for dynamic loading.
    """
    return EnvDetector().detect(old_yaml, new_yaml)