"""Pydantic models for Crossref API entities."""

from .agency import Agency, WorkAgency
from .base import (
    Contributor,
    CrossRefDate,
    FunderRef,
    IssnType,
    LicenseRef,
)
from .datacitation import DataCitation, DataCitationEnd
from .entities import CrossRefType, Funder, Journal, License, Member, Prefix
from .safe_types import SafeInt, SafeList, SafeStr, SafeStrList
from .work import Work

__all__ = [
    "Agency",
    "Contributor",
    "CrossRefDate",
    "CrossRefType",
    "DataCitation",
    "DataCitationEnd",
    "Funder",
    "FunderRef",
    "IssnType",
    "Journal",
    "License",
    "LicenseRef",
    "Member",
    "Prefix",
    "SafeInt",
    "SafeList",
    "SafeStr",
    "SafeStrList",
    "Work",
    "WorkAgency",
]
