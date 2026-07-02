import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CPUDetector:
    """
    Analyzes Kubernetes YAML to detect changes in CPU requests and limits.
    """

    def _parse_cpu(self, cpu_str: str) -> float:
        """
        Converts standard Kubernetes CPU strings (e.g., '100m', '1', '0.5') to a comparable float.
        """
        if not cpu_str or str(cpu_str).lower() in ["none", "missing"]:
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
        """
        Extracts CPU requests and limits mapping container names to their configurations.
        """
        cpu_configs = {}
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])

            for container in containers:
                if isinstance(container, dict):
                    name = container.get("name", "unknown")
                    resources = container.get("resources", {})
                    
                    requests = resources.get("requests", {}).get("cpu", "Missing")
                    limits = resources.get("limits", {}).get("cpu", "Missing")
                    
                    cpu_configs[name] = {
                        "request": str(requests),
                        "limit": str(limits)
                    }
        except AttributeError:
            pass
            
        return cpu_configs

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares old and new YAML configurations for CPU changes.
        
        Rules:
        1. Request Reduced -> MEDIUM
        2. Limit Reduced -> HIGH
        3. Limit Increased -> LOW
        4. Missing Resources -> HIGH
        5. Unchanged -> NONE
        """
        try:
            old_cpu = self._extract_cpu_resources(old_yaml)
            new_cpu = self._extract_cpu_resources(new_yaml)

            changes_detected = False
            severity_score = 0
            
            old_reqs, old_lims = [], []
            new_reqs, new_lims = [], []
            reasons = []

            all_containers = set(old_cpu.keys()).union(set(new_cpu.keys()))

            for container in all_containers:
                old_config = old_cpu.get(container, {"request": "Missing", "limit": "Missing"})
                new_config = new_cpu.get(container, {"request": "Missing", "limit": "Missing"})
                
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
                        reasons.append(f"'{container}' is missing CPU request or limit.")
                        continue
                        
                    # Compare numerical values
                    old_req_val = self._parse_cpu(old_config["request"])
                    new_req_val = self._parse_cpu(new_config["request"])
                    
                    old_lim_val = self._parse_cpu(old_config["limit"])
                    new_lim_val = self._parse_cpu(new_config["limit"])
                    
                    # Evaluate Limit rules first
                    if new_lim_val < old_lim_val:
                        severity_score = max(severity_score, 3) # HIGH
                        reasons.append(f"'{container}' limit reduced.")
                    elif new_lim_val > old_lim_val:
                        severity_score = max(severity_score, 1) # LOW
                        reasons.append(f"'{container}' limit increased.")
                        
                    # Evaluate Request rules
                    if new_req_val < old_req_val:
                        severity_score = max(severity_score, 2) # MEDIUM
                        reasons.append(f"'{container}' request reduced.")
                    elif new_req_val > old_req_val:
                        # Ensure we flag that a change happened, even if not mapped to a specific severity increase
                        if severity_score == 0:
                            reasons.append(f"'{container}' request increased.")

            if not changes_detected:
                return {
                    "field": "cpu",
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
                    "reason": "No changes in CPU resources.",
                    "recommendation": ""
                }

            # Map score back to severity string
            severity_map = {0: "NONE", 1: "LOW", 2: "MEDIUM", 3: "HIGH"}
            severity = severity_map.get(severity_score, "NONE")
            
            # Map recommendation based on highest severity
            if severity == "HIGH":
                recommendation = "Reducing CPU limits or missing resources can cause severe throttling. Define explicit resources."
            elif severity == "MEDIUM":
                recommendation = "Reducing CPU requests may affect pod scheduling and guarantees. Verify application requirements."
            elif severity == "LOW":
                recommendation = "Monitor Node capacity to ensure sufficient CPU exists for the new limits."
            else:
                recommendation = ""

            return {
                "field": "cpu",
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
            logger.error(f"Error while detecting CPU changes: {str(e)}")
            return {
                "field": "cpu",
                "old_value": {"request": "None", "limit": "None"},
                "new_value": {"request": "None", "limit": "None"},
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing CPU resources.",
                "recommendation": ""
            }

# Expose the detect function at the module level for dynamic discovery by analyzer.py
def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return CPUDetector().detect(old_yaml, new_yaml)
