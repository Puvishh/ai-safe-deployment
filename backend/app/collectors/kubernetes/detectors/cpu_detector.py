import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CpuDetector:
    """
    Analyzes Kubernetes YAML to detect changes in CPU requests and limits.
    """

    def _parse_cpu(self, cpu_str: str) -> float:
        """
        Converts standard Kubernetes CPU strings (e.g., '100m', '1', '0.5') to a comparable float.
        """
        if not cpu_str or cpu_str == "None":
            return 0.0
        
        cpu_str = str(cpu_str).strip()
        if cpu_str.endswith('m'):
            try:
                return float(cpu_str[:-1]) / 1000.0
            except ValueError:
                return 0.0
        try:
            return float(cpu_str)
        except ValueError:
            return 0.0

    def _extract_cpu_resources(self, yaml_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        cpu_configs = {}
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])

            for container in containers:
                name = container.get("name", "unknown")
                resources = container.get("resources", {})
                
                requests = resources.get("requests", {}).get("cpu", "None")
                limits = resources.get("limits", {}).get("cpu", "None")
                
                cpu_configs[name] = {
                    "requests": str(requests),
                    "limits": str(limits)
                }
        except AttributeError:
            pass
            
        return cpu_configs

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares old and new YAML configurations for CPU changes.
        
        Rules:
        - Reduced CPU -> HIGH
        - Increased CPU -> LOW
        - Unchanged -> NONE
        """
        try:
            old_cpu = self._extract_cpu_resources(old_yaml)
            new_cpu = self._extract_cpu_resources(new_yaml)

            changes_detected = False
            cpu_reduced = False
            cpu_increased = False
            
            old_vals = []
            new_vals = []
            changes_summary = []

            all_containers = set(old_cpu.keys()).union(set(new_cpu.keys()))

            for container in all_containers:
                old_config = old_cpu.get(container, {"requests": "None", "limits": "None"})
                new_config = new_cpu.get(container, {"requests": "None", "limits": "None"})
                
                if old_config != new_config:
                    changes_detected = True
                    
                    old_str = f"req:{old_config['requests']}/lim:{old_config['limits']}"
                    new_str = f"req:{new_config['requests']}/lim:{new_config['limits']}"
                    
                    old_vals.append(f"{container}: {old_str}")
                    new_vals.append(f"{container}: {new_str}")
                    changes_summary.append(f"{container} ({old_str} -> {new_str})")
                    
                    for res_type in ["requests", "limits"]:
                        old_val = self._parse_cpu(old_config[res_type])
                        new_val = self._parse_cpu(new_config[res_type])
                        
                        if new_val < old_val:
                            cpu_reduced = True
                        elif new_val > old_val:
                            cpu_increased = True

            if not changes_detected:
                return {
                    "field": "resources.cpu",
                    "old_value": " | ".join(old_vals) if old_vals else "None",
                    "new_value": " | ".join(new_vals) if new_vals else "None",
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No changes in CPU resources.",
                    "recommendation": ""
                }

            if cpu_reduced:
                severity = "HIGH"
                reason = f"CPU resources reduced for: {', '.join(changes_summary)}"
                recommendation = "Reducing CPU can lead to severe throttling. Verify application profiling data."
            elif cpu_increased:
                severity = "LOW"
                reason = f"CPU resources increased for: {', '.join(changes_summary)}"
                recommendation = "Monitor Node capacity to ensure sufficient CPU exists for the new limits."
            else:
                severity = "NONE"
                reason = "CPU string representation changed but computed values remain identical."
                recommendation = ""

            return {
                "field": "resources.cpu",
                "old_value": " | ".join(old_vals),
                "new_value": " | ".join(new_vals),
                "changed": True,
                "severity": severity,
                "reason": reason,
                "recommendation": recommendation
            }
            
        except Exception as e:
            logger.error(f"Error while detecting CPU changes: {str(e)}")
            return {
                "field": "resources.cpu",
                "old_value": None,
                "new_value": None,
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing CPU resources.",
                "recommendation": ""
            }

def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return CpuDetector().detect(old_yaml, new_yaml)
