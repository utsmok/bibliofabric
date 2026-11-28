"""Pydantic models for the Title Word Abbreviation table."""

from pydantic import BaseModel, ConfigDict, Field

_CONFIG = ConfigDict(extra="allow", populate_by_name=True)


class LtwaEntry(BaseModel):
    """One row of the Title Word Abbreviation table.

    ``abbreviation`` is ``None`` when the Portal shows no abbreviation for
    the word (the cell then reads ``None``, a Portal rendering quirk).
    """

    word: str
    abbreviation: str | None = None
    language: str | None = None

    model_config = _CONFIG


class LtwaPage(BaseModel):
    """One parsed page of the Title Word Abbreviation table."""

    entries: list[LtwaEntry] = Field(default_factory=list)
    page: int
    page_size: int
    search: str | None = None
    languages: list[str] = Field(default_factory=list)
    sort: str
    order: str

    model_config = _CONFIG


__all__ = ["LtwaEntry", "LtwaPage"]
