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
        for numerical comparison.
        """
        if not mem_str or mem_str.lower() in ["none", "missing"]:
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
        Extracts memory requests and limits mapping container names to their configurations.
        """
        memory_configs = {}
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])

            for container in containers:
                if isinstance(container, dict):
                    name = container.get("name", "unknown")
                    resources = container.get("resources", {})
                    
                    requests = resources.get("requests", {}).get("memory", "Missing")
                    limits = resources.get("limits", {}).get("memory", "Missing")
                    
                    memory_configs[name] = {
                        "request": str(requests),
                        "limit": str(limits)
                    }
        except AttributeError:
            pass
            
        return memory_configs

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares old and new YAML configurations for memory changes.
        
        Rules:
        1. Request Reduced -> MEDIUM
        2. Limit Reduced -> HIGH
        3. Limit Increased -> LOW
        4. Missing Resources -> HIGH
        5. Unchanged -> NONE
        """
        try:
            old_mem = self._extract_memory_resources(old_yaml)
            new_mem = self._extract_memory_resources(new_yaml)

            changes_detected = False
            severity_score = 0
            
            old_reqs, old_lims = [], []
            new_reqs, new_lims = [], []
            reasons = []

            all_containers = set(old_mem.keys()).union(set(new_mem.keys()))

            for container in all_containers:
                old_config = old_mem.get(container, {"request": "Missing", "limit": "Missing"})
                new_config = new_mem.get(container, {"request": "Missing", "limit": "Missing"})
                
                # Append to strings for display output
                old_reqs.append(f"{container}: {old_config['request']}")
                old_lims.append(f"{container}: {old_config['limit']}")
                new_reqs.append(f"{container}: {new_config['request']}")
                new_lims.append(f"{container}: {new_config['limit']}")
                
                if old_config != new_config:
                    changes_detected = True
                    
                    # Detect missing resources in new config
                    if new_config['request'] == "Missing" or new_config['limit'] == "Missing":
                        severity_score = max(severity_score, 3) # HIGH
                        reasons.append(f"'{container}' is missing memory request or limit.")
                        continue
                        
                    # Compare numerical values
                    old_req_bytes = self._parse_memory(old_config["request"])
                    new_req_bytes = self._parse_memory(new_config["request"])
                    
                    old_lim_bytes = self._parse_memory(old_config["limit"])
                    new_lim_bytes = self._parse_memory(new_config["limit"])
                    
                    # Evaluate Limit rules first
                    if new_lim_bytes < old_lim_bytes:
                        severity_score = max(severity_score, 3) # HIGH
                        reasons.append(f"'{container}' limit reduced.")
                    elif new_lim_bytes > old_lim_bytes:
                        severity_score = max(severity_score, 1) # LOW
                        reasons.append(f"'{container}' limit increased.")
                        
                    # Evaluate Request rules
                    if new_req_bytes < old_req_bytes:
                        severity_score = max(severity_score, 2) # MEDIUM
                        reasons.append(f"'{container}' request reduced.")
                    elif new_req_bytes > old_req_bytes:
                        # Ensure we flag that a change happened, even if not explicitly defined in severity rules
                        if severity_score == 0:
                            reasons.append(f"'{container}' request increased.")

            if not changes_detected:
                return {
                    "field": "memory",
                    "old_value": {
                        "request": " | ".join(old_reqs) if old_reqs else "None",
                        "limit": " | ".join(old_lims) if old_lims else "None"
                    },
                    "new_value": {
                        "request": " | ".join(new_reqs) if new_reqs else "None",
                        "limit": " | ".join(new_lims) if new_lims else "None"
                    },
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No changes in memory resources.",
                    "recommendation": ""
                }

            # Map score back to severity string
            severity_map = {0: "NONE", 1: "LOW", 2: "MEDIUM", 3: "HIGH"}
            severity = severity_map.get(severity_score, "NONE")
            
            # Map recommendation based on highest severity
            if severity == "HIGH":
                recommendation = "Reducing limits or missing resources can cause OOMKilled events. Define explicit resources."
            elif severity == "MEDIUM":
                recommendation = "Reducing requests may affect node scheduling. Verify application profile."
            elif severity == "LOW":
                recommendation = "Monitor Node capacity to ensure sufficient resources exist for the new limits."
            else:
                recommendation = ""

            return {
                "field": "memory",
                "old_value": {
                    "request": " | ".join(old_reqs),
                    "limit": " | ".join(old_lims)
                },
                "new_value": {
                    "request": " | ".join(new_reqs),
                    "limit": " | ".join(new_lims)
                },
                "changed": True,
                "severity": severity,
                "reason": " ".join(reasons),
                "recommendation": recommendation
            }
            
        except Exception as e:
            logger.error(f"Error while detecting memory changes: {str(e)}")
            return {
                "field": "memory",
                "old_value": {"request": "None", "limit": "None"},
                "new_value": {"request": "None", "limit": "None"},
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing memory resources.",
                "recommendation": ""
            }

# Expose the detect function at the module level for dynamic discovery by analyzer.py
def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return MemoryDetector().detect(old_yaml, new_yaml)
