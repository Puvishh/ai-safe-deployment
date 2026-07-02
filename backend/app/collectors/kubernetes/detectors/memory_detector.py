import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MemoryDetector:
    """
    Analyzes Kubernetes YAML to detect changes in memory requests and limits.
    """

    def _parse_memory(self, mem_str: str) -> float:
        """
        Converts standard Kubernetes memory strings (e.g., 256Mi, 1Gi) to bytes
        for numeric comparison.
        """
        if not mem_str or mem_str == "None":
            return 0.0
        
        mem_str = str(mem_str).strip()
        if mem_str.isdigit():
            return float(mem_str)
            
        suffixes = {
            'Ei': 1024**6, 'Pi': 1024**5, 'Ti': 1024**4, 'Gi': 1024**3, 'Mi': 1024**2, 'Ki': 1024,
            'E': 1000**6, 'P': 1000**5, 'T': 1000**4, 'G': 1000**3, 'M': 1000**2, 'k': 1000,
            'm': 0.001
        }
        
        for suffix, multiplier in suffixes.items():
            if mem_str.endswith(suffix):
                try:
                    val = float(mem_str[:-len(suffix)])
                    return val * multiplier
                except ValueError:
                    return 0.0
                    
        return 0.0

    def _extract_memory_resources(self, yaml_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """
        Helper function to safely extract memory requests and limits.
        """
        memory_configs = {}
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])

            for container in containers:
                name = container.get("name", "unknown")
                resources = container.get("resources", {})
                
                requests = resources.get("requests", {}).get("memory", "None")
                limits = resources.get("limits", {}).get("memory", "None")
                
                memory_configs[name] = {
                    "requests": requests,
                    "limits": limits
                }
        except AttributeError:
            pass
            
        return memory_configs

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares old and new YAML configurations for memory changes.
        
        Rules:
        - Reduced memory -> HIGH
        - Increased memory -> LOW
        - Unchanged -> NONE
        """
        try:
            old_mem = self._extract_memory_resources(old_yaml)
            new_mem = self._extract_memory_resources(new_yaml)

            changes_detected = False
            memory_reduced = False
            memory_increased = False
            
            old_vals = []
            new_vals = []
            changes_summary = []

            all_containers = set(old_mem.keys()).union(set(new_mem.keys()))

            for container in all_containers:
                old_config = old_mem.get(container, {"requests": "None", "limits": "None"})
                new_config = new_mem.get(container, {"requests": "None", "limits": "None"})
                
                if old_config != new_config:
                    changes_detected = True
                    
                    old_str = f"req:{old_config['requests']}/lim:{old_config['limits']}"
                    new_str = f"req:{new_config['requests']}/lim:{new_config['limits']}"
                    
                    old_vals.append(f"{container}: {old_str}")
                    new_vals.append(f"{container}: {new_str}")
                    changes_summary.append(f"{container} ({old_str} -> {new_str})")
                    
                    # Compare bytes to determine if reduced or increased
                    for res_type in ["requests", "limits"]:
                        old_bytes = self._parse_memory(old_config[res_type])
                        new_bytes = self._parse_memory(new_config[res_type])
                        
                        if new_bytes < old_bytes:
                            memory_reduced = True
                        elif new_bytes > old_bytes:
                            memory_increased = True

            if not changes_detected:
                return {
                    "field": "resources.memory",
                    "old_value": " | ".join(old_vals) if old_vals else "None",
                    "new_value": " | ".join(new_vals) if new_vals else "None",
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No changes in memory resources.",
                    "recommendation": ""
                }

            # Apply severity rules
            if memory_reduced:
                severity = "HIGH"
                reason = f"Memory resources reduced for: {', '.join(changes_summary)}"
                recommendation = "Reducing memory can lead to OOMKilled events. Verify application profiling data."
            elif memory_increased:
                severity = "LOW"
                reason = f"Memory resources increased for: {', '.join(changes_summary)}"
                recommendation = "Monitor Node capacity to ensure sufficient resources exist for the new limits."
            else:
                # Fallback if bytes are equal but string representation changed
                severity = "NONE"
                reason = "Memory string representation changed but computed bytes remain identical."
                recommendation = ""

            return {
                "field": "resources.memory",
                "old_value": " | ".join(old_vals),
                "new_value": " | ".join(new_vals),
                "changed": True,
                "severity": severity,
                "reason": reason,
                "recommendation": recommendation
            }
            
        except Exception as e:
            logger.error(f"Error while detecting memory changes: {str(e)}")
            return {
                "field": "resources.memory",
                "old_value": None,
                "new_value": None,
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing memory resources.",
                "recommendation": ""
            }

# Expose the detect function at the module level for dynamic discovery by analyzer.py
def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return MemoryDetector().detect(old_yaml, new_yaml)
