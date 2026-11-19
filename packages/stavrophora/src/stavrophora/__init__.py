"""Stavrophora: Python interface for the Crossref API."""

try:
    from importlib.metadata import PackageNotFoundError, version as _get_version

    __version__ = _get_version("stavrophora")
except PackageNotFoundError:
    __version__ = "0.0.0"

from bibliofabric import Page
from bibliofabric.exceptions import (
    APIError,
    AuthError,
    BibliofabricError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)

from .client import StavrophoraClient
from .config import StavrophoraSettings, get_settings
from .filters import FunderFilters, MemberFilters, WorksFilters
from .models import (
    Agency,
    Contributor,
    CrossRefDate,
    CrossRefType,
    Funder,
    FunderRef,
    IssnType,
    Journal,
    License,
    LicenseRef,
    Member,
    Prefix,
    Work,
    WorkAgency,
)

__all__ = [
    "__version__",
    "Agency",
    "APIError",
    "AuthError",
    "BibliofabricError",
    "ConfigurationError",
    "Contributor",
    "CrossRefDate",
    "CrossRefType",
    "Funder",
    "FunderFilters",
    "FunderRef",
    "get_settings",
    "IssnType",
    "Journal",
    "License",
    "LicenseRef",
    "Member",
    "MemberFilters",
    "NetworkError",
    "NotFoundError",
    "Page",
    "Prefix",
    "RateLimitError",
    "StavrophoraClient",
    "StavrophoraSettings",
    "TimeoutError",
    "ValidationError",
    "Work",
    "WorkAgency",
    "WorksFilters",
]
