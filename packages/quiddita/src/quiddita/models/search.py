"""Models for ``wbsearchentities`` results."""

from pydantic import BaseModel, ConfigDict


class _SearchModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class EntitySearchResult(_SearchModel):
    """One hit of a ``wbsearchentities`` response."""

    id: str
    label: str | None = None
    match: dict[str, str] | None = None
    description: str | None = None
    aliases: list[str] | None = None
    display_language: str | None = None
    concepturi: str | None = None


__all__ = ["EntitySearchResult"]
