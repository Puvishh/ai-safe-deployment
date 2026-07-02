import logging
from typing import Dict, Any, List, Set

logger = logging.getLogger(__name__)

class SecretDetector:
    """
    Analyzes Kubernetes YAML to detect changes in Secret references.
    """

    def _extract_secrets(self, yaml_data: Dict[str, Any]) -> Set[str]:
        secrets = set()
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            
            volumes: List[Dict[str, Any]] = template_spec.get("volumes", [])
            for vol in volumes:
                if "secret" in vol and "secretName" in vol["secret"]:
                    secrets.add(vol["secret"]["secretName"])
                    
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])
            for container in containers:
                env_from = container.get("envFrom", [])
                for ref in env_from:
                    if "secretRef" in ref and "name" in ref["secretRef"]:
                        secrets.add(ref["secretRef"]["name"])
                        
        except AttributeError:
            pass
            
        return secrets

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects additions or removals of Secret references in the deployment.
        Any change is flagged as HIGH severity.
        """
        try:
            old_secrets = self._extract_secrets(old_yaml)
            new_secrets = self._extract_secrets(new_yaml)

            if old_secrets == new_secrets:
                return {
                    "field": "secretRef",
                    "old_value": ", ".join(sorted(old_secrets)) if old_secrets else "None",
                    "new_value": ", ".join(sorted(new_secrets)) if new_secrets else "None",
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No changes in Secret dependencies.",
                    "recommendation": ""
                }
                
            added = new_secrets - old_secrets
            removed = old_secrets - new_secrets
            
            changes = []
            if added:
                changes.append(f"Added: {', '.join(added)}")
            if removed:
                changes.append(f"Removed: {', '.join(removed)}")

            return {
                "field": "secretRef",
                "old_value": ", ".join(sorted(old_secrets)) if old_secrets else "None",
                "new_value": ", ".join(sorted(new_secrets)) if new_secrets else "None",
                "changed": True,
                "severity": "HIGH",
                "reason": f"Secret dependencies changed: {'; '.join(changes)}",
                "recommendation": "Ensure newly referenced Secrets are securely provisioned. Verify least privilege."
            }
            
        except Exception as e:
            logger.error(f"Error while detecting Secret changes: {str(e)}")
            return {
                "field": "secretRef",
                "old_value": None,
                "new_value": None,
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing Secret references.",
                "recommendation": ""
            }

def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return SecretDetector().detect(old_yaml, new_yaml)
