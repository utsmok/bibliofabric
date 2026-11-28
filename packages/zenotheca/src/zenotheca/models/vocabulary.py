"""Pydantic models for Zenodo vocabulary entries."""

from typing import Any

from bibliofabric import SafeList, SafeStr
from pydantic import BaseModel, ConfigDict


class ZenothecaVocabulary(BaseModel):
    """One entry of a Zenodo vocabulary (``resourcetypes``, ``licenses``, ...).

    ``title`` and ``description`` map language codes to texts; ``props``
    carries the vocabulary-specific extra properties (``schema.org``,
    ``datacite_general``, ``alpha_2``, ...).
    """

    id: SafeStr | None = None
    type: SafeStr | None = None
    revision_id: int | None = None
    created: str | None = None
    updated: str | None = None
    title: dict[str, str] | None = None
    description: dict[str, str] | None = None
    icon: str | None = None
    tags: SafeList[str] = []
    props: dict[str, Any] | None = None
    links: dict[str, str] = {}

    model_config = ConfigDict(extra="allow")

    @property
    def english_title(self) -> str | None:
        """The ``en`` title, else the first title the entry carries."""
        if not self.title:
            return None
        return self.title.get("en") or next(iter(self.title.values()))


__all__ = ["ZenothecaVocabulary"]
