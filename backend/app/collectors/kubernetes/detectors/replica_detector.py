import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ReplicaDetector:
    """
    Analyzes Kubernetes YAML to detect changes in the replica count.
    """

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares the old and new YAML configurations for changes in spec.replicas.
        
        Rules:
        - Replica reduced -> HIGH severity
        - Replica increased -> LOW severity
        - No change -> NONE severity
        """
        try:
            old_spec = old_yaml.get("spec", {})
            new_spec = new_yaml.get("spec", {})

            # Use 1 as the default replica count if not specified
            old_replicas = old_spec.get("replicas", 1)
            new_replicas = new_spec.get("replicas", 1)

            if old_replicas == new_replicas:
                return {
                    "field": "spec.replicas",
                    "old_value": old_replicas,
                    "new_value": new_replicas,
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No change in replica count.",
                    "recommendation": ""
                }

            # Determine if reduced or increased
            if new_replicas < old_replicas:
                severity = "HIGH"
                reason = "Replica count reduced. This may reduce application availability."
                recommendation = "Maintain at least 2 replicas for production deployments."
            else:
                severity = "LOW"
                reason = "Replica count increased."
                recommendation = "Ensure underlying nodes have sufficient capacity to handle the increased load."

            return {
                "field": "spec.replicas",
                "old_value": old_replicas,
                "new_value": new_replicas,
                "changed": True,
                "severity": severity,
                "reason": reason,
                "recommendation": recommendation
            }

        except Exception as e:
            logger.error(f"Error while detecting replica changes: {str(e)}")
            # Return a safe fallback
            return {
                "field": "spec.replicas",
                "old_value": None,
                "new_value": None,
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing replica count.",
                "recommendation": ""
            }

# Expose the detect function at the module level for dynamic discovery by analyzer.py
def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return ReplicaDetector().detect(old_yaml, new_yaml)
