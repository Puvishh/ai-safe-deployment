"""
Deployment Context Builder

Converts Git analysis into deployment context.
"""

from app.schemes.git import GitAnalyzeResponse


class DeploymentContextBuilder:
    """
    Builds deployment context from Git analysis.
    """

    def build(self, git_data: GitAnalyzeResponse) -> dict:

        deployment_files = []
        docker_files = []
        config_files = []
        source_files = []
        documentation_files = []
        other_files = []

        for file in git_data.changes:

            if file.category.value == "kubernetes":
                deployment_files.append(file.path)

            elif file.category.value == "docker":
                docker_files.append(file.path)

            elif file.category.value == "config":
                config_files.append(file.path)

            elif file.category.value == "source_code":
                source_files.append(file.path)

            elif file.category.value == "documentation":
                documentation_files.append(file.path)

            else:
                other_files.append(file.path)

        return {
            "repository": git_data.repository.name,
            "branch": git_data.repository.branch,

            "deployment_files": deployment_files,

            # Temporary paths for MVP
            "kubernetes": {
                "old_yaml": "test-repositories/sample_k8/k8s/deployment_old.yaml",
                "new_yaml": "test-repositories/sample_k8/k8s/deployment.yaml",
            },

            "docker_files": docker_files,
            "config_files": config_files,
            "source_files": source_files,
            "documentation_files": documentation_files,
            "other_files": other_files,
            "total_changed_files": len(git_data.changes),
        }