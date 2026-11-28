"""Pydantic models for the parsed HTML search result page of the Portal."""

from pydantic import BaseModel, ConfigDict, Field

_CONFIG = ConfigDict(extra="allow", populate_by_name=True)


class OtherMedium(BaseModel):
    """One "Other Medium" link of a search hit (a sibling medium of the cluster)."""

    label: str
    href: str

    model_config = _CONFIG


class SearchHit(BaseModel):
    """One record row of the Portal search result page.

    The fields mirror what the row shows: the ISSN, its medium and country,
    the key title with a link into ``/resource``, the ISSN-L and ISSN-H
    cluster ids, cancelled ISSNs of the record, and the sibling media of the
    cluster.
    """

    issn: str | None = None
    issn_l: str | None = None
    issn_h: str | None = None
    title: str | None = None
    category: str | None = None
    category_label: str | None = None
    medium: str | None = None
    medium_label: str | None = None
    country: str | None = None
    country_label: str | None = None
    cancelled_issns: list[str] = Field(default_factory=list)
    other_media: list[OtherMedium] = Field(default_factory=list)
    detail_path: str | None = None

    model_config = _CONFIG


class SearchPage(BaseModel):
    """One parsed page of the Portal search result list."""

    total: int | None = None
    page: int
    page_size: int
    hits: list[SearchHit] = Field(default_factory=list)

    model_config = _CONFIG


__all__ = ["OtherMedium", "SearchHit", "SearchPage"]
