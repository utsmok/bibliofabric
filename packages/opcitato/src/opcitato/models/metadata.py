"""Models of the Meta API rows."""

from bibliofabric import SafeStr
from pydantic import BaseModel, ConfigDict

from ..ids import ParsedIdentifier, parse_identifiers


def _split_persons(field: str) -> list[str]:
    """Split a semicolon-separated author or editor field into entries."""
    return [entry.strip() for entry in field.split(";") if entry.strip()]


class MetadataRecord(BaseModel):
    """One bibliographic metadata row of the Meta API.

    ``id`` holds all known identifiers of the entity, space-separated and
    prefixed (``doi:10.1038/nature12373 pmid:23903748 omid:br/06120344846``).
    ``author`` and ``editor`` are semicolon-separated lists of person
    strings such as ``Peroni, Silvio [orcid:0000-0003-0530-4305
    omid:ra/0614010840729]``; ``venue`` is the venue title followed by its
    identifiers in brackets. Missing values are empty strings.
    """

    id: SafeStr
    title: SafeStr = ""
    author: SafeStr = ""
    editor: SafeStr = ""
    pub_date: SafeStr = ""
    issue: SafeStr = ""
    volume: SafeStr = ""
    venue: SafeStr = ""
    page: SafeStr = ""
    type: SafeStr = ""
    publisher: SafeStr = ""

    model_config = ConfigDict(extra="allow")

    @property
    def identifiers(self) -> list[ParsedIdentifier]:
        """The identifiers of the entity, parsed from ``id``."""
        return parse_identifiers(self.id)

    @property
    def authors(self) -> list[str]:
        """The ``author`` field split into person strings."""
        return _split_persons(self.author)

    @property
    def editors(self) -> list[str]:
        """The ``editor`` field split into person strings."""
        return _split_persons(self.editor)


__all__ = ["MetadataRecord"]
