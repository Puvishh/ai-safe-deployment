import logging
import importlib
import pkgutil
from typing import Dict, Any, List

from .yaml_reader import YamlReader
from . import detectors

logger = logging.getLogger(__name__)

class KubernetesAnalyzer:
    """
    Orchestrates the execution of all Kubernetes deployment detectors.
    Loads YAML content, runs analysis rules, and aggregates risk metrics.
    """

    def __init__(self):
        """Initializes the analyzer by discovering and loading all available detectors."""
        self.detectors = self._load_detectors()

    def _load_detectors(self) -> List[Any]:
        """
        Dynamically discovers all detector classes within the 'detectors' package.
        Assumes each module ending with '_detector' has a module-level 'detect' function
        that instantiates the class and runs its logic.
        """
        loaded_detectors = []
        try:
            for _, module_name, _ in pkgutil.iter_modules(detectors.__path__):
                if module_name.endswith("_detector"):
                    module = importlib.import_module(f".detectors.{module_name}", package=__package__)
                    if hasattr(module, 'detect') and callable(module.detect):
                        loaded_detectors.append(module.detect)
                    else:
                        logger.warning(f"Module {module_name} lacks a callable 'detect' function.")
        except Exception as e:
            logger.error(f"Error loading detectors: {str(e)}")
            
        logger.info(f"Loaded {len(loaded_detectors)} detectors.")
        return loaded_detectors

    def _calculate_risk(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates the aggregate risk score and determining the overall risk level.
        """
        score = 0
        severity_weights = {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
            "NONE": 0
        }

        for finding in findings:
            severity = finding.get("severity", "NONE")
            score += severity_weights.get(severity, 0)

        # Determine risk level based on the accumulated score
        if score >= 10:
            level = "CRITICAL"
        elif score >= 5:
            level = "HIGH"
        elif score >= 3:
            level = "MEDIUM"
        elif score >= 1:
            level = "LOW"
        else:
            level = "NONE"

        return {
            "score": score,
            "level": level
        }

    def analyze(self, old_yaml_str: str, new_yaml_str: str, is_file_path: bool = False) -> Dict[str, Any]:
        """
        Loads the YAML configurations, executes all detectors, and builds the final risk report.

        Args:
            old_yaml_str: The string content or file path of the old YAML.
            new_yaml_str: The string content or file path of the new YAML.
            is_file_path: If True, treats the inputs as file paths instead of string content.

        Returns:
            Dict[str, Any]: A consolidated risk analysis report.
        """
        # Load YAML using YamlReader
        if is_file_path:
            old_yaml = YamlReader.read_from_file(old_yaml_str) or {}
            new_yaml = YamlReader.read_from_file(new_yaml_str) or {}
        else:
            old_yaml = YamlReader.read_from_string(old_yaml_str) or {}
            new_yaml = YamlReader.read_from_string(new_yaml_str) or {}

        findings = []
        recommendations = []

        if not old_yaml and not new_yaml:
            logger.warning("Both YAML configurations are empty or failed to parse.")
            return {
                "risk_score": 0,
                "risk_level": "NONE",
                "findings": [],
                "recommendations": ["Ensure valid YAML configurations are provided."]
            }

        # Execute all dynamically loaded detectors
        for detect_func in self.detectors:
            try:
                result = detect_func(old_yaml, new_yaml)
                
                # Only include results that actually triggered a change detection
                if result and result.get("changed") is True:
                    findings.append(result)
                    
                    rec = result.get("recommendation")
                    if rec and rec not in recommendations:
                        recommendations.append(rec)
            except Exception as e:
                detector_name = getattr(detect_func, '__module__', 'UnknownDetector')
                logger.error(f"Detector {detector_name} failed: {str(e)}")

        # Calculate final risk metrics based on findings
        risk = self._calculate_risk(findings)

        return {
            "risk_score": risk["score"],
            "risk_level": risk["level"],
            "findings": findings,
            "recommendations": recommendations
        }
