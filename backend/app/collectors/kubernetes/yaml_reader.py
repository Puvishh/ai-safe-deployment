import logging
import yaml
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class YamlReader:
    """
    A utility class to read and parse Kubernetes YAML files.
    Responsible solely for loading YAML strings or files into Python dictionaries
    and handling potential parsing errors safely.
    """

    @staticmethod
    def read_from_file(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Reads a YAML file from the given file path and parses it.

        Args:
            file_path (str): The absolute or relative path to the YAML file.

        Returns:
            Optional[Dict[str, Any]]: The parsed YAML as a dictionary, or None if an error occurs.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return YamlReader.read_from_string(file.read())
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None
        except IOError as e:
            logger.error(f"IO Error reading file {file_path}: {str(e)}")
            return None

    @staticmethod
    def read_from_string(yaml_content: str) -> Optional[Dict[str, Any]]:
        """
        Parses a YAML string into a Python dictionary.

        Args:
            yaml_content (str): The YAML content as a string.

        Returns:
            Optional[Dict[str, Any]]: The parsed YAML as a dictionary, or None if an error occurs.
        """
        if not yaml_content or not yaml_content.strip():
            logger.warning("Empty YAML content provided.")
            return None

        try:
            # safe_load avoids arbitrary code execution vulnerabilities
            parsed_data = yaml.safe_load(yaml_content)
            
            if not isinstance(parsed_data, dict):
                logger.error("Parsed YAML is not a dictionary. Kubernetes manifests should be dictionaries.")
                return None
                
            return parsed_data
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML content: {str(e)}")
            return None
