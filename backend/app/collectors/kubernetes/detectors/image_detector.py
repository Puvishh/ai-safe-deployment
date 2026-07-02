import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ImageDetector:
    """
    Analyzes Kubernetes YAML to detect changes in container images.
    """

    def _extract_images(self, yaml_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Helper function to safely extract container names and their images.
        """
        images = {}
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])

            for container in containers:
                name = container.get("name", "unknown")
                image = container.get("image")
                if image:
                    images[name] = image
        except AttributeError:
            pass
        
        return images

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares the old and new YAML configurations for changes in images.
        
        Rules:
        - latest tag -> HIGH severity
        - image version changed -> MEDIUM severity
        - unchanged -> NONE severity
        """
        try:
            old_images = self._extract_images(old_yaml)
            new_images = self._extract_images(new_yaml)

            changes_detected = False
            has_latest = False
            
            old_vals = []
            new_vals = []
            
            # Check for changes in existing or newly added containers
            for container_name, new_img in new_images.items():
                old_img = old_images.get(container_name)
                
                if old_img != new_img:
                    changes_detected = True
                    # In Docker/K8s, no tag implicitly means latest
                    if new_img and (new_img.endswith(":latest") or ":" not in new_img.split("/")[-1]):
                        has_latest = True
                        
                old_display = old_img if old_img else "None"
                old_vals.append(f"{container_name}: {old_display}")
                new_vals.append(f"{container_name}: {new_img}")
                
            # Check for removed containers
            for container_name, old_img in old_images.items():
                if container_name not in new_images:
                    changes_detected = True
                    old_vals.append(f"{container_name}: {old_img}")
                    new_vals.append(f"{container_name}: Removed")

            if not changes_detected:
                return {
                    "field": "image",
                    "old_value": " | ".join(old_vals) if old_vals else "None",
                    "new_value": " | ".join(new_vals) if new_vals else "None",
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No changes in container images.",
                    "recommendation": ""
                }

            if has_latest:
                severity = "HIGH"
                reason = "Image updated to use 'latest' tag (or no tag). This introduces non-deterministic deployments."
                recommendation = "Pin images to specific versions or SHA digests."
            else:
                severity = "MEDIUM"
                reason = "Image version changed."
                recommendation = "Ensure new image tags have been security scanned and approved for deployment."

            return {
                "field": "image",
                "old_value": " | ".join(old_vals),
                "new_value": " | ".join(new_vals),
                "changed": True,
                "severity": severity,
                "reason": reason,
                "recommendation": recommendation
            }
            
        except Exception as e:
            logger.error(f"Error while detecting image changes: {str(e)}")
            return {
                "field": "image",
                "old_value": None,
                "new_value": None,
                "changed": False,
                "severity": "NONE",
                "reason": "Error processing container images.",
                "recommendation": ""
            }

# Expose the detect function at the module level for dynamic discovery by analyzer.py
def detect(old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
    return ImageDetector().detect(old_yaml, new_yaml)
