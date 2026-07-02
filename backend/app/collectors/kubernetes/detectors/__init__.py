"""
Kubernetes Detectors Package

This package contains individual detector modules for analyzing specific
changes in Kubernetes YAML configurations. 

Each module MUST:
1. End with the suffix '_detector.py'
2. Expose a function with the exact signature:
   `def detect(old_yaml: dict, new_yaml: dict) -> dict:`

The orchestrator (`analyzer.py`) will automatically discover and execute
all valid detectors placed in this directory.
"""
