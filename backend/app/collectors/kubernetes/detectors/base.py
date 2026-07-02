from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseDetector(ABC):
    """
    Abstract base class for all Kubernetes detectors.
    """

    @abstractmethod
    def detect(
        self,
        old_yaml: Dict[str, Any],
        new_yaml: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze the old and new Kubernetes manifests and return
        a structured result.
        """
        pass