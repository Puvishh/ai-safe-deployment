"""
Git Collector API Schemas

This module contains the request and response models used by the
Git Collector API.

Author: AI Safe Deployment
"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


# ==========================================================
# ENUMS
# ==========================================================

class FileStatus(str, Enum):
    """Supported Git file statuses."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    UNTRACKED = "untracked"


class FileCategory(str, Enum):
    """Supported deployment file categories."""

    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    TERRAFORM = "terraform"
    HELM = "helm"
    CONFIG = "config"
    SOURCE_CODE = "source_code"
    DOCUMENTATION = "documentation"
    OTHER = "other"


# ==========================================================
# REQUEST MODEL
# ==========================================================

class GitAnalyzeRequest(BaseModel):
    """
    Request model for Git repository analysis.
    """

    repository_path: str = Field(
        ...,
        description="Absolute or relative path to the local Git repository.",
        examples=["C:/Projects/payment-service"],
    )


# ==========================================================
# RESPONSE MODELS
# ==========================================================

class ChangedFile(BaseModel):
    """
    Represents a single changed file inside a Git repository.
    """

    path: str = Field(
        ...,
        description="Relative file path from repository root.",
        examples=["k8s/deployment.yaml"],
    )

    status: FileStatus = Field(
        ...,
        description="Git change status of the file.",
    )

    category: FileCategory = Field(
        ...,
        description="Detected deployment file category.",
    )


class RepositoryInfo(BaseModel):
    """
    Metadata about the Git repository.
    """

    name: str = Field(
        ...,
        description="Repository name.",
        examples=["payment-service"],
    )

    branch: str = Field(
        ...,
        description="Current active Git branch.",
        examples=["main"],
    )

    latest_commit: str = Field(
        ...,
        description="Latest Git commit hash.",
        examples=["e8b72cf91c1a"],
    )

    author: str = Field(
        ...,
        description="Latest commit author.",
        examples=["Puvisha Asokan"],
    )

    latest_commit_message: str = Field(
        ...,
        description="Latest commit message.",
        examples=["Updated deployment configuration"],
    )


class GitAnalyzeResponse(BaseModel):
    """
    Response returned after Git repository analysis.
    """

    success: bool = Field(
        ...,
        description="Indicates whether analysis completed successfully.",
        examples=[True],
    )

    repository: RepositoryInfo = Field(
        ...,
        description="Repository metadata.",
    )

    changes: List[ChangedFile] = Field(
        default_factory=list,
        description="List of changed files detected in the repository.",
    )


# ==========================================================
# ERROR RESPONSE
# ==========================================================

class ErrorResponse(BaseModel):
    """
    Standard API error response.
    """

    success: bool = False

    message: str = Field(
        ...,
        description="Error message.",
        examples=["Repository not found."],
    )