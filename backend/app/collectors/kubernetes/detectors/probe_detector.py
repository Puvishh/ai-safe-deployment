import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ProbeDetector:
    """
    Analyzes Kubernetes YAML to detect changes in container health probes
    (livenessProbe, readinessProbe, startupProbe).
    """

    def _extract_probes(self, yaml_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Safely extracts health probes for all containers in the configuration.
        Returns a dictionary mapping container names to their probe configurations.
        """
        probes_config = {}
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])

            for container in containers:
                if isinstance(container, dict):
                    name = container.get("name", "unknown")
                    probes_config[name] = {
                        "livenessProbe": container.get("livenessProbe"),
                        "readinessProbe": container.get("readinessProbe"),
                        "startupProbe": container.get("startupProbe")
                    }
        except AttributeError:
            pass
            
        return probes_config

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares old and new YAML configurations for probe changes.
        
        Rules:
        - Probe Removed -> HIGH
        - Probe Modified -> MEDIUM
        - Probe Added -> LOW
        - No Change -> NONE
        """
        try:
            old_probes = self._extract_probes(old_yaml)
            new_probes = self._extract_probes(new_yaml)

            changes_detected = False
            severity_score = 0
            
            old_vals = []
            new_vals = []
            reasons = []
            affected_probe_types = set()

            all_containers = set(old_probes.keys()).union(set(new_probes.keys()))

            for container in all_containers:
                old_config = old_probes.get(container, {"livenessProbe": None, "readinessProbe": None, "startupProbe": None})
                new_config = new_probes.get(container, {"livenessProbe": None, "readinessProbe": None, "startupProbe": None})
                
                for probe_type in ["livenessProbe", "readinessProbe", "startupProbe"]:
                    old_probe = old_config.get(probe_type)
                    new_probe = new_config.get(probe_type)
                    
                    if old_probe != new_probe:
                        changes_detected = True
                        affected_probe_types.add(probe_type)
                        
                        # Serialize for display output
                        old_str = json.dumps(old_probe, sort_keys=True) if old_probe else "None"
                        new_str = json.dumps(new_probe, sort_keys=True) if new_probe else "None"
                        
                        old_vals.append(f"{container}.{probe_type}: {old_str}")
                        new_vals.append(f"{container}.{probe_type}: {new_str}")
                        
                        # Apply severity rules
                        if old_probe and not new_probe:
                            severity_score = max(severity_score, 3) # HIGH (Removed)
                            reasons.append(f"'{container}' {probe_type} removed.")
                        elif not old_probe and new_probe:
                            severity_score = max(severity_score, 1) # LOW (Added)
                            reasons.append(f"'{container}' {probe_type} added.")
                        else:
                            severity_score = max(severity_score, 2) # MEDIUM (Modified)
                            reasons.append(f"'{container}' {probe_type} modified (e.g., delay, period, timeout, or thresholds).")

            if not changes_detected:
                return {
                    "field": "probe",
                    "probe_type": "None",
                    "old_value": "None",
                    "new_value": "None",
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No changes in container probes.",
                    "recommendation": ""
                }

            # Map score back to severity string
            severity_map = {0: "NONE", 1: "LOW", 2: "MEDIUM", 3: "HIGH"}
            severity = severity_map.get(severity_score, "NONE")
            
            # Formulate recommendation based on severity
            if severity == "HIGH":
                recommendation = "Removing probes removes the ability for Kubernetes to automatically recover failed containers. Ensure this is intentional."
            elif severity == "MEDIUM":
                recommendation = "Verify that modified probe timings (delays, timeouts, thresholds) align with application startup and response characteristics."
            elif severity == "LOW":
                recommendation = "Ensure the application correctly implements the newly added health check endpoints."
            else:
                recommendation = ""

            return {
                "field": "probe",
                "probe_type": ", ".join(sorted(affected_probe_types)),
                "old_value": " | ".join(old_vals),
                "new_value": " | ".join(new_vals),
                "changed": True,
                "severity": severity,
                "reason": " ".join(reasons),
                "recommendation": recommendation
            }
            
        except Exception as e:
            logger.error(f"Error while detecting probe changes: {str(e)}")
            return {
                "field": "probe",
                "probe_type": "Unknown",
                "old_value": "None",
                "new_value": "None",
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing container probes.",
                "recommendation": ""
            }

# Expose the detect function at the module level for dynamic discovery by analyzer.py
def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return ProbeDetector().detect(old_yaml, new_yaml)
