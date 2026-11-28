"""Pydantic models for the Semantic Scholar Datasets API.

A release is a dated snapshot of the whole Academic Graph. Dataset
metadata lists the pre-signed file URLs of one release; diffs carry the
update and delete files between two releases.
"""

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict


class DatasetSummary(BaseModel):
    """One dataset of a release, with its schema README."""

    name: SafeStr | None = None
    description: SafeStr | None = None
    README: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class Release(BaseModel):
    """One dated release of the Academic Graph datasets.

    ``release_id`` is the date string (for example ``2026-11-24``); the
    release listing route answers plain id strings without metadata.
    """

    release_id: SafeStr | None = None
    datasets: SafeList[DatasetSummary] = []
    README: SafeStr | None = None

    model_config = ConfigDict(extra="allow")


class DatasetMetadata(BaseModel):
    """One dataset of one release, with its pre-signed file URLs.

    ``files`` holds temporary download links; this route needs an API key
    and answers HTTP 401 without one.
    """

    name: SafeStr | None = None
    description: SafeStr | None = None
    README: SafeStr | None = None
    files: SafeList[str] = []

    model_config = ConfigDict(extra="allow")


class DatasetDiff(BaseModel):
    """The changes between two releases of one dataset.

    The Datasets API names these fields in snake_case, unlike the graph.
    """

    from_release: SafeStr | None = None
    to_release: SafeStr | None = None
    update_files: SafeList[str] = []
    delete_files: SafeList[str] = []

    model_config = ConfigDict(extra="allow")


class DatasetDiffList(BaseModel):
    """The diffs that bring one dataset from one release to another."""

    dataset: SafeStr | None = None
    start_release: SafeStr | None = None
    end_release: SafeStr | None = None
    diffs: SafeList[DatasetDiff] = []

    model_config = ConfigDict(extra="allow")


__all__ = [
    "DatasetDiff",
    "DatasetDiffList",
    "DatasetMetadata",
    "DatasetSummary",
    "Release",
]
