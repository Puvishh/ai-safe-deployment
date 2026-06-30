"""
Git File Classifier

This module classifies changed files into deployment-related categories.

Author: AI Safe Deployment
"""

from pathlib import Path

from app.schemes.git import FileCategory 


class GitFileClassifier:
    """
    Classifies changed files based on file name and extension.
    """

    KUBERNETES_FILES = {
        "deployment.yaml",
        "deployment.yml",
        "service.yaml",
        "service.yml",
        "ingress.yaml",
        "ingress.yml",
        "statefulset.yaml",
        "daemonset.yaml",
        "configmap.yaml",
        "secret.yaml",
        "namespace.yaml",
    }

    CONFIG_FILES = {
        ".env",
        ".env.example",
        "application.yml",
        "application.yaml",
        "application.properties",
        "config.yml",
        "config.yaml",
    }

    DOCUMENTATION_EXTENSIONS = {
        ".md",
        ".txt",
        ".rst",
    }

    SOURCE_CODE_EXTENSIONS = {
        ".py",
        ".java",
        ".js",
        ".ts",
        ".go",
        ".cpp",
        ".c",
        ".cs",
        ".rb",
        ".php",
    }

    def classify(self, file_path: str) -> FileCategory:
        """
        Classify a file into one of the supported categories.
        """

        path = Path(file_path)

        filename = path.name.lower()

        extension = path.suffix.lower()

        # Kubernetes
        if filename in self.KUBERNETES_FILES or "k8s" in file_path.lower():
            return FileCategory.KUBERNETES

        # Docker
        if filename == "dockerfile" or "docker-compose" in filename:
            return FileCategory.DOCKER

        # Terraform
        if extension == ".tf" or ".terraform" in file_path.lower():
            return FileCategory.TERRAFORM

        # Helm
        if "chart.yaml" == filename:
            return FileCategory.HELM

        if "values.yaml" == filename:
            return FileCategory.HELM

        if "templates" in file_path.lower():
            return FileCategory.HELM

        # Config
        if filename in self.CONFIG_FILES:
            return FileCategory.CONFIG

        # Documentation
        if extension in self.DOCUMENTATION_EXTENSIONS:
            return FileCategory.DOCUMENTATION

        # Source Code
        if extension in self.SOURCE_CODE_EXTENSIONS:
            return FileCategory.SOURCE_CODE

        return FileCategory.OTHER