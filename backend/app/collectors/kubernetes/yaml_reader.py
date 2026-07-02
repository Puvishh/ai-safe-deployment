import logging
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class KubernetesYAMLReader:
    """
    Reads Kubernetes YAML manifests.
    """

    def read_yaml(self, file_path: str) -> Any:
        """
        Read a Kubernetes YAML file.

        Supports single-document and multi-document YAML.
        """

        try:

            with open(file_path, "r", encoding="utf-8") as file:

                documents = list(yaml.safe_load_all(file))

            return documents

        except FileNotFoundError as e:

            logger.error(f"YAML file not found: {file_path}")
            raise e

        except yaml.YAMLError as e:

            logger.error(f"Invalid YAML: {e}")
            raise e