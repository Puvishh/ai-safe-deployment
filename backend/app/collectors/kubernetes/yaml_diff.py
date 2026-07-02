"""
Kubernetes YAML Diff

Reads Kubernetes YAML files and extracts deployment information.
Version 1: Reads replica count and container image.
"""

from pathlib import Path
import yaml


class KubernetesYAMLDiff:
    """
    Reads Kubernetes deployment YAML files.
    """

    def load_yaml(self, file_path: str) -> dict:
        """
        Load a YAML file and return it as a Python dictionary.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def get_replicas(self, file_path: str) -> int:
        """
        Extract the replica count from a Deployment YAML.
        """

        data = self.load_yaml(file_path)

        return data.get("spec", {}).get("replicas", 1)

    def get_image(self, file_path: str) -> str:
        """
        Extract the container image from Deployment YAML.
        """

        data = self.load_yaml(file_path)

        containers = (
            data.get("spec", {})
                .get("template", {})
                .get("spec", {})
                .get("containers", [])
        )

        if not containers:
            return ""

        return containers[0].get("image", "")

    def read_replicas(self, old_file: str, new_file: str) -> dict:
        """
        Read replica values from two deployment YAML files.
        """

        old_replicas = self.get_replicas(old_file)
        new_replicas = self.get_replicas(new_file)

        return {
            "field": "spec.replicas",
            "old": old_replicas,
            "new": new_replicas,
        }

    def compare_replicas(self, old_file: str, new_file: str) -> dict:
        """
        Compare replica counts between two deployment YAML files.
        """

        old_replicas = self.get_replicas(old_file)
        new_replicas = self.get_replicas(new_file)

        changed = old_replicas != new_replicas

        if changed:
            if new_replicas < old_replicas:
                severity = "HIGH"
                reason = "Replica count reduced. This may reduce application availability."
            else:
                severity = "LOW"
                reason = "Replica count increased."
        else:
            severity = "NONE"
            reason = "Replica count unchanged."

        return {
            "field": "spec.replicas",
            "old": old_replicas,
            "new": new_replicas,
            "changed": changed,
            "severity": severity,
            "reason": reason,
        }

    def compare_image(self, old_file: str, new_file: str) -> dict:
        """
        Compare container images.
        """

        old_image = self.get_image(old_file)
        new_image = self.get_image(new_file)

        changed = old_image != new_image

        if not changed:
            severity = "NONE"
            reason = "Container image unchanged."
        elif new_image.endswith(":latest"):
            severity = "HIGH"
            reason = "Using 'latest' image tag in production is not recommended."
        else:
            severity = "MEDIUM"
            reason = "Container image version changed."

        return {
            "field": "image",
            "old": old_image,
            "new": new_image,
            "changed": changed,
            "severity": severity,
            "reason": reason,
        }