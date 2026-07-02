import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ImageDetector:
    """
    Analyzes Kubernetes YAML to detect changes in container images.
    """

    def _extract_images(self, yaml_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Safely extracts container names and their corresponding image strings.
        Returns a dictionary mapping container names to their images.
        """
        images = {}
        try:
            spec = yaml_data.get("spec", {})
            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers: List[Dict[str, Any]] = template_spec.get("containers", [])

            for container in containers:
                if isinstance(container, dict):
                    name = container.get("name", "unknown")
                    # If image key is missing, default to empty string to represent 'Missing image'
                    image = container.get("image", "")
                    images[name] = image
        except AttributeError:
            pass
        
        return images

    def detect(self, old_yaml: Dict[str, Any], new_yaml: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compares the old and new YAML configurations for changes in images.
        
        Rules:
        1. Image unchanged -> NONE
        2. Image version changed -> MEDIUM
        3. Image changed to latest -> HIGH
        4. Missing image -> HIGH
        """
        try:
            old_images = self._extract_images(old_yaml)
            new_images = self._extract_images(new_yaml)

            changes_detected = False
            
            # Use numeric values to track highest severity across multiple containers
            severity_score = 0 
            
            old_vals = []
            new_vals = []
            reasons = []

            # Check new containers for changes, latest tags, or missing images
            for container_name, new_img in new_images.items():
                old_img = old_images.get(container_name)
                
                old_display = old_img if old_img else "None"
                new_display = new_img if new_img else "Missing"
                
                if old_img != new_img:
                    changes_detected = True
                    old_vals.append(f"{container_name}: {old_display}")
                    new_vals.append(f"{container_name}: {new_display}")
                    
                    if not new_img:
                        severity_score = max(severity_score, 2)
                        reasons.append(f"Container '{container_name}' is missing an image definition.")
                    elif new_img.endswith(":latest") or ":" not in new_img.split("/")[-1]:
                        severity_score = max(severity_score, 2)
                        reasons.append(f"Container '{container_name}' changed to use 'latest' tag.")
                    else:
                        severity_score = max(severity_score, 1)
                        reasons.append(f"Container '{container_name}' image version changed.")

            # Check for removed containers
            for container_name, old_img in old_images.items():
                if container_name not in new_images:
                    changes_detected = True
                    old_vals.append(f"{container_name}: {old_img}")
                    new_vals.append(f"{container_name}: Removed")
                    severity_score = max(severity_score, 1)
                    reasons.append(f"Container '{container_name}' was removed.")

            if not changes_detected:
                return {
                    "field": "spec.template.spec.containers.image",
                    "old_value": " | ".join(old_vals) if old_vals else "None",
                    "new_value": " | ".join(new_vals) if new_vals else "None",
                    "changed": False,
                    "severity": "NONE",
                    "reason": "No changes in container images.",
                    "recommendation": ""
                }

            # Map score back to severity string
            severity = "HIGH" if severity_score == 2 else "MEDIUM"
            
            if severity == "HIGH":
                recommendation = "Ensure all containers have explicitly pinned image versions or SHAs."
            else:
                recommendation = "Ensure new image tags have been security scanned and approved."

            return {
                "field": "spec.template.spec.containers.image",
                "old_value": " | ".join(old_vals),
                "new_value": " | ".join(new_vals),
                "changed": True,
                "severity": severity,
                "reason": " ".join(reasons),
                "recommendation": recommendation
            }
            
        except Exception as e:
            logger.error(f"Error while detecting image changes: {str(e)}")
            return {
                "field": "spec.template.spec.containers.image",
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
