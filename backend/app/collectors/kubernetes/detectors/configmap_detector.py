import logging
from typing import Dict, Any, List, Set

logger = logging.getLogger(__name__)

class ConfigMapDetector:
    """
    Analyzes Kubernetes YAML to detect changes in ConfigMap references.
    """

    def _extract_configmaps(self, yaml_data: Dict[str, Any]) -> Set[str]:
        configmaps = set()
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            
            volumes: List[Dict[str, Any]] = template_spec.get("volumes", [])
            for vol in volumes:
                if "configMap" in vol and "name" in vol["configMap"]:
                    configmaps.add(vol["configMap"]["name"])
                    
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])
            for container in containers:
                env_from = container.get("envFrom", [])
                for ref in env_from:
                    if "configMapRef" in ref and "name" in ref["configMapRef"]:
                        configmaps.add(ref["configMapRef"]["name"])
                        
        except AttributeError:
            pass
            
        return configmaps

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects additions or removals of ConfigMap references in the deployment.
        Any change is flagged as LOW severity.
        """
        try:
            old_cms = self._extract_configmaps(old_yaml)
            new_cms = self._extract_configmaps(new_yaml)

            if old_cms == new_cms:
                return {
                    "field": "configMapRef",
                    "old_value": ", ".join(sorted(old_cms)) if old_cms else "None",
                    "new_value": ", ".join(sorted(new_cms)) if new_cms else "None",
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No changes in ConfigMap dependencies.",
                    "recommendation": ""
                }
                
            added = new_cms - old_cms
            removed = old_cms - new_cms
            
            changes = []
            if added:
                changes.append(f"Added: {', '.join(added)}")
            if removed:
                changes.append(f"Removed: {', '.join(removed)}")

            return {
                "field": "configMapRef",
                "old_value": ", ".join(sorted(old_cms)) if old_cms else "None",
                "new_value": ", ".join(sorted(new_cms)) if new_cms else "None",
                "changed": True,
                "severity": "LOW",
                "reason": f"ConfigMap dependencies changed: {'; '.join(changes)}",
                "recommendation": "Ensure newly referenced ConfigMaps exist in the cluster before deployment."
            }
            
        except Exception as e:
            logger.error(f"Error while detecting ConfigMap changes: {str(e)}")
            return {
                "field": "configMapRef",
                "old_value": None,
                "new_value": None,
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing ConfigMap references.",
                "recommendation": ""
            }

def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return ConfigMapDetector().detect(old_yaml, new_yaml)
