import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EnvDetector:
    """
    Analyzes Kubernetes YAML to detect changes in environment variables.
    """

    def _extract_env_vars(self, yaml_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        env_configs = {}
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])

            for container in containers:
                name = container.get("name", "unknown")
                envs = container.get("env", [])
                
                container_env = {}
                for env_item in envs:
                    if isinstance(env_item, dict) and "name" in env_item:
                        env_name = env_item["name"]
                        env_val = env_item.get("value")
                        if env_val is None and "valueFrom" in env_item:
                            env_val = json.dumps(env_item["valueFrom"], sort_keys=True)
                        container_env[env_name] = str(env_val)
                        
                env_configs[name] = container_env
        except AttributeError:
            pass
            
        return env_configs

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects changes in environment variables across all containers.
        Any change is flagged as MEDIUM severity.
        """
        try:
            old_envs = self._extract_env_vars(old_yaml)
            new_envs = self._extract_env_vars(new_yaml)

            changes_detected = False
            changes = []
            old_vals = []
            new_vals = []

            all_containers = set(old_envs.keys()).union(set(new_envs.keys()))

            for container in all_containers:
                old_container_env = old_envs.get(container, {})
                new_container_env = new_envs.get(container, {})
                
                all_keys = set(old_container_env.keys()).union(set(new_container_env.keys()))
                
                for key in all_keys:
                    old_val = old_container_env.get(key, "Not_Set")
                    new_val = new_container_env.get(key, "Not_Set")
                    
                    if old_val != new_val:
                        changes_detected = True
                        changes.append(f"{container}.{key}")
                        old_vals.append(f"{container}.{key}: {old_val}")
                        new_vals.append(f"{container}.{key}: {new_val}")

            if not changes_detected:
                return {
                    "field": "env",
                    "old_value": " | ".join(old_vals) if old_vals else "None",
                    "new_value": " | ".join(new_vals) if new_vals else "None",
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No changes in environment variables.",
                    "recommendation": ""
                }

            return {
                "field": "env",
                "old_value": " | ".join(old_vals),
                "new_value": " | ".join(new_vals),
                "changed": True,
                "severity": "MEDIUM",
                "reason": f"Environment variables changed for: {', '.join(changes)}",
                "recommendation": "Verify that new or updated environment variables do not expose sensitive data directly."
            }
            
        except Exception as e:
            logger.error(f"Error while detecting env changes: {str(e)}")
            return {
                "field": "env",
                "old_value": None,
                "new_value": None,
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing environment variables.",
                "recommendation": ""
            }

def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return EnvDetector().detect(old_yaml, new_yaml)
