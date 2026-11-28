"""Pydantic models for the ROR data dumps hosted on Zenodo."""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict, Field


class DumpFileLinks(BaseModel):
    """Links of one dump file; ``self_url`` downloads the file content."""

    download: SafeStr | None = None
    self_url: SafeStr | None = Field(default=None, alias="self")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class DumpFile(BaseModel):
    """One file of a Zenodo dump record (``key``, ``size`` in bytes, ``checksum``)."""

    key: SafeStr | None = None
    size: int | None = None
    checksum: SafeStr | None = None
    links: DumpFileLinks | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class DumpMetadata(BaseModel):
    """The Zenodo record metadata of a dump (title, version, publication date)."""

    title: SafeStr | None = None
    publication_date: str | None = None
    version: SafeStr | None = None
    doi: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class DumpLinks(BaseModel):
    """Links of a Zenodo dump record."""

    self_url: SafeStr | None = Field(default=None, alias="self")
    self_html: SafeStr | None = None
    latest: SafeStr | None = None
    latest_html: SafeStr | None = None
    parent: SafeStr | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class RorDump(BaseModel):
    """One versioned ROR data dump (a Zenodo record of the ``ror-data`` community).

    ``record_id`` is the Zenodo record id, ``version`` the ROR data release
    (for example ``v2.16``), and ``files`` the downloadable files, normally
    one zip holding a JSON and a CSV serialization of every record.
    """

    record_id: int | None = Field(default=None, alias="id")
    concept_id: int | None = Field(default=None, alias="conceptrecid")
    doi: SafeStr | None = None
    created: str | None = None
    updated: str | None = None
    metadata: DumpMetadata | None = None
    files: SafeList[DumpFile] = []
    links: DumpLinks | None = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    @property
    def title(self) -> str | None:
        """The record title (``ROR Data``)."""
        return self.metadata.title if self.metadata is not None else None

    @property
    def publication_date(self) -> str | None:
        """The ISO date the dump was published."""
        return self.metadata.publication_date if self.metadata is not None else None

    @property
    def version(self) -> str | None:
        """The ROR data release version (for example ``v2.16``)."""
        return self.metadata.version if self.metadata is not None else None

    @property
    def zip_file(self) -> DumpFile | None:
        """The first ``.zip`` file of the dump, or ``None`` when there is none."""
        return next(
            (file for file in self.files if (file.key or "").endswith(".zip")), None
        )

    @property
    def zip_url(self) -> str | None:
        """The download URL of the zip file, or ``None`` when it is unknown."""
        zip_file = self.zip_file
        if zip_file is None or zip_file.links is None:
            return None
        return zip_file.links.self_url or zip_file.links.download


__all__ = ["DumpFile", "DumpFileLinks", "DumpLinks", "DumpMetadata", "RorDump"]
