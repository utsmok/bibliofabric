"""Typed resource clients for the Crossref routes."""

from .funders import FundersResource
from .journals import JournalsResource
from .licenses import LicensesResource
from .members import MembersResource
from .prefixes import PrefixesResource
from .types import TypesResource
from .works import ScopedWorksResource, WorksResource

__all__ = [
    "FundersResource",
    "JournalsResource",
    "LicensesResource",
    "MembersResource",
    "PrefixesResource",
    "ScopedWorksResource",
    "TypesResource",
    "WorksResource",
]
