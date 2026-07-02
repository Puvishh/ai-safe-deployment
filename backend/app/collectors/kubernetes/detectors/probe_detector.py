import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ProbeDetector:
    """
    Analyzes Kubernetes YAML to detect changes in container health probes.
    """

    def _extract_probes(self, yaml_data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        probes_config = {}
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])

            for container in containers:
                name = container.get("name", "unknown")
                liveness = container.get("livenessProbe")
                readiness = container.get("readinessProbe")
                startup = container.get("startupProbe")
                
                probes_config[name] = {
                    "liveness": json.dumps(liveness, sort_keys=True) if liveness else "None",
                    "readiness": json.dumps(readiness, sort_keys=True) if readiness else "None",
                    "startup": json.dumps(startup, sort_keys=True) if startup else "None"
                }
        except AttributeError:
            pass
            
        return probes_config

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects changes in livenessProbe, readinessProbe, and startupProbe.
        Any change is flagged as HIGH severity.
        """
        try:
            old_probes = self._extract_probes(old_yaml)
            new_probes = self._extract_probes(new_yaml)

            changes_detected = False
            changes = []
            old_vals = []
            new_vals = []

            all_containers = set(old_probes.keys()).union(set(new_probes.keys()))

            for container in all_containers:
                old_config = old_probes.get(container, {"liveness": "None", "readiness": "None", "startup": "None"})
                new_config = new_probes.get(container, {"liveness": "None", "readiness": "None", "startup": "None"})
                
                for probe_type in ["liveness", "readiness", "startup"]:
                    if old_config[probe_type] != new_config[probe_type]:
                        changes_detected = True
                        changes.append(f"{container} {probe_type} changed")
                        old_vals.append(f"{container}.{probe_type}: {old_config[probe_type]}")
                        new_vals.append(f"{container}.{probe_type}: {new_config[probe_type]}")

            if not changes_detected:
                return {
                    "field": "probes",
                    "old_value": " | ".join(old_vals) if old_vals else "None",
                    "new_value": " | ".join(new_vals) if new_vals else "None",
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No changes in container probes.",
                    "recommendation": ""
                }

            return {
                "field": "probes",
                "old_value": " | ".join(old_vals),
                "new_value": " | ".join(new_vals),
                "changed": True,
                "severity": "HIGH",
                "reason": f"Health check probes changed: {', '.join(changes)}",
                "recommendation": "Review probe timings and endpoints to avoid unwanted container restarts or traffic loss."
            }
            
        except Exception as e:
            logger.error(f"Error while detecting probe changes: {str(e)}")
            return {
                "field": "probes",
                "old_value": None,
                "new_value": None,
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing container probes.",
                "recommendation": ""
            }

def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return ProbeDetector().detect(old_yaml, new_yaml)
