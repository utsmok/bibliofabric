"""Pydantic models for Zenodo communities."""

from typing import Any

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict


class ZenothecaCommunityOrganization(BaseModel):
    """One organization behind a community (``id``, ``name``, ``identifiers``)."""

    id: SafeStr | None = None
    name: SafeStr | None = None
    identifiers: SafeList[dict[str, str]] = []

    model_config = ConfigDict(extra="allow")


class ZenothecaCommunityType(BaseModel):
    """The community type (``id`` ``project``, ``title`` in several languages)."""

    id: SafeStr | None = None
    title: dict[str, str] | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaCommunityMetadata(BaseModel):
    """The ``metadata`` block of a community."""

    title: SafeStr | None = None
    description: str | None = None
    type: ZenothecaCommunityType | None = None
    website: str | None = None
    organizations: SafeList[ZenothecaCommunityOrganization] = []

    model_config = ConfigDict(extra="allow")


class ZenothecaDeletionStatus(BaseModel):
    """Whether the community was deleted (``is_deleted`` plus a ``status`` code)."""

    is_deleted: bool | None = None
    status: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaCommunity(BaseModel):
    """One Zenodo community.

    ``id`` is the stable UUID the API routes accept; ``slug`` is the short
    name (``ror-data``) that the ``/communities/{slug}`` routes and the
    ``communities`` parameter of the records search accept too.
    """

    id: SafeStr | None = None
    slug: SafeStr | None = None
    created: str | None = None
    updated: str | None = None
    metadata: ZenothecaCommunityMetadata | None = None
    access: dict[str, Any] | None = None
    children: dict[str, Any] | None = None
    custom_fields: dict[str, Any] | None = None
    deletion_status: ZenothecaDeletionStatus | None = None
    revision_id: int | None = None
    links: dict[str, str] = {}

    model_config = ConfigDict(extra="allow")


__all__ = [
    "ZenothecaCommunity",
    "ZenothecaCommunityMetadata",
    "ZenothecaCommunityOrganization",
    "ZenothecaCommunityType",
    "ZenothecaDeletionStatus",
]
