"""Pydantic models for Zenodo records, versions, and files."""

from typing import Any

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict


class ZenothecaCreator(BaseModel):
    """One creator of a record; ``affiliation`` is ``None`` on newer records."""

    name: SafeStr | None = None
    affiliation: str | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaContributor(BaseModel):
    """One contributor of a record, typed by ``type`` (``ContactPerson``, ...)."""

    name: SafeStr | None = None
    affiliation: str | None = None
    type: SafeStr | None = None
    orcid: str | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaRelatedIdentifier(BaseModel):
    """One related identifier of a record (``identifier``, ``relation``, ``scheme``)."""

    identifier: SafeStr | None = None
    relation: SafeStr | None = None
    scheme: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaLicense(BaseModel):
    """The license of a record (``cc-zero``, ``cc-by-4.0``, ...)."""

    id: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaDate(BaseModel):
    """One date of a record (``type`` plus ``start``/``end`` where present)."""

    type: SafeStr | None = None
    start: str | None = None
    end: str | None = None
    description: str | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaResourceType(BaseModel):
    """The resource type of a record (``type`` ``dataset``, ``title`` ``Dataset``)."""

    id: str | None = None
    title: str | None = None
    type: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaCommunityRef(BaseModel):
    """A community a record belongs to (``{"id": "ror-data"}``)."""

    id: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaVersionInfo(BaseModel):
    """The version-family entry of ``metadata.relations.version``.

    ``parent.pid_value`` is the concept id shared by every version of the
    record; ``index`` counts the versions from 1 and ``is_last`` marks the
    newest.
    """

    index: int | None = None
    is_last: bool | None = None
    parent: dict[str, Any] | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaRelations(BaseModel):
    """The ``relations`` block of the metadata; Zenodo fills ``version``."""

    version: SafeList[ZenothecaVersionInfo] = []

    model_config = ConfigDict(extra="allow")


class ZenothecaRecordMetadata(BaseModel):
    """The ``metadata`` block of a record.

    Legacy deposit fields (``journal``, ``part_of``, ``thesis``, ...),
    granted fields, and any field added upstream are kept through
    ``extra="allow"``.
    """

    title: SafeStr | None = None
    doi: str | None = None
    publication_date: str | None = None
    description: str | None = None
    access_right: SafeStr | None = None
    version: str | None = None
    creators: SafeList[ZenothecaCreator] = []
    contributors: SafeList[ZenothecaContributor] = []
    keywords: SafeList[str] = []
    license: ZenothecaLicense | None = None
    dates: SafeList[ZenothecaDate] = []
    communities: SafeList[ZenothecaCommunityRef] = []
    related_identifiers: SafeList[ZenothecaRelatedIdentifier] = []
    relations: ZenothecaRelations | None = None
    resource_type: ZenothecaResourceType | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def concept_id(self) -> str | None:
        """The concept id from ``relations.version[0].parent.pid_value``, if any."""
        for info in (self.relations or ZenothecaRelations()).version:
            parent = info.parent or {}
            if str(parent.get("pid_value", "")):
                return str(parent["pid_value"])
        return None


class ZenothecaFile(BaseModel):
    """One file entry embedded in a record (``key``, ``size``, ``checksum``)."""

    id: SafeStr | None = None
    key: SafeStr | None = None
    size: int | None = None
    checksum: SafeStr | None = None
    links: dict[str, str] = {}

    model_config = ConfigDict(extra="allow")


class ZenothecaStats(BaseModel):
    """Usage statistics of a record, per version and overall."""

    downloads: int | None = None
    unique_downloads: int | None = None
    views: int | None = None
    unique_views: int | None = None
    version_downloads: int | None = None
    version_unique_downloads: int | None = None
    version_views: int | None = None
    version_unique_views: int | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaOwner(BaseModel):
    """The user that owns a record (``{"id": "73440"}``)."""

    id: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class ZenothecaRecord(BaseModel):
    """One Zenodo record (a published version of a concept).

    ``id`` is the numeric version id, ``conceptrecid`` the id of the version
    family, and ``recid`` repeats ``id`` as a string. ``state`` is ``done``
    on published records and ``status`` is ``published``. ``links`` maps the
    related routes (``self``, ``latest``, ``versions``, ``parent``,
    ``files``, ...).
    """

    id: int | None = None
    recid: SafeStr | None = None
    conceptrecid: SafeStr | None = None
    conceptdoi: str | None = None
    doi: str | None = None
    doi_url: str | None = None
    title: SafeStr | None = None
    created: str | None = None
    modified: str | None = None
    updated: str | None = None
    state: SafeStr | None = None
    status: SafeStr | None = None
    submitted: bool | None = None
    revision: int | None = None
    owners: SafeList[ZenothecaOwner] = []
    stats: ZenothecaStats | None = None
    files: SafeList[ZenothecaFile] = []
    links: dict[str, Any] = {}
    metadata: ZenothecaRecordMetadata | None = None

    model_config = ConfigDict(extra="allow")

    @property
    def concept_id(self) -> str | None:
        """The concept id (``conceptrecid``), shared by every version."""
        return self.conceptrecid or None


class ZenothecaFileEntry(BaseModel):
    """One entry of the ``/records/{id}/files`` listing.

    Carries more detail than the file list embedded in a record:
    ``mimetype``, ``version_id``, ``bucket_id``, and ``links`` with the
    ``self``, ``content``, and ``container`` routes.
    """

    key: SafeStr | None = None
    size: int | None = None
    checksum: SafeStr | None = None
    mimetype: str | None = None
    status: SafeStr | None = None
    storage_class: str | None = None
    created: str | None = None
    updated: str | None = None
    version_id: str | None = None
    file_id: str | None = None
    bucket_id: str | None = None
    metadata: dict[str, Any] | None = None
    access: dict[str, Any] | None = None
    transfer: dict[str, Any] | None = None
    links: dict[str, str] = {}

    model_config = ConfigDict(extra="allow")


class ZenothecaFiles(BaseModel):
    """The answer of ``GET /records/{id}/files``."""

    enabled: bool | None = None
    default_preview: str | None = None
    order: SafeList[str] = []
    entries: SafeList[ZenothecaFileEntry] = []
    links: dict[str, str] = {}

    model_config = ConfigDict(extra="allow")

    @property
    def keys(self) -> list[str]:
        """The file keys in ``order`` when set, else the ``entries`` order."""
        if self.order:
            return list(self.order)
        return [entry.key or "" for entry in self.entries]


__all__ = [
    "ZenothecaCommunityRef",
    "ZenothecaContributor",
    "ZenothecaCreator",
    "ZenothecaDate",
    "ZenothecaFile",
    "ZenothecaFileEntry",
    "ZenothecaFiles",
    "ZenothecaLicense",
    "ZenothecaOwner",
    "ZenothecaRecord",
    "ZenothecaRecordMetadata",
    "ZenothecaRelatedIdentifier",
    "ZenothecaRelations",
    "ZenothecaResourceType",
    "ZenothecaStats",
    "ZenothecaVersionInfo",
]
