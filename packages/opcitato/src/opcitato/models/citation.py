"""Models of the Index API rows."""

from bibliofabric import SafeStr
from pydantic import BaseModel, ConfigDict

from ..ids import ParsedIdentifier, parse_identifiers


class Citation(BaseModel):
    """One citation row of the Index API.

    ``citing`` and ``cited`` hold the identifiers of the citing and the
    cited entity, space-separated and each prefixed with its scheme
    (``omid:br/06120344846 doi:10.1038/nature12373 pmid:23903748``).
    ``creation`` is the publication date of the citing entity in ISO format
    and may be partial (``2013`` or ``2013-07``). ``timespan`` is the XSD
    duration between the publication dates and can be negative
    (``-P1Y1M16D``). ``journal_sc`` and ``author_sc`` are ``"yes"`` or
    ``"no"`` strings that report a journal self-citation and an author
    self-citation.
    """

    oci: SafeStr
    citing: SafeStr
    cited: SafeStr
    creation: SafeStr = ""
    timespan: SafeStr = ""
    journal_sc: SafeStr = ""
    author_sc: SafeStr = ""

    model_config = ConfigDict(extra="allow")

    @property
    def citing_identifiers(self) -> list[ParsedIdentifier]:
        """The identifiers of the citing entity, parsed from ``citing``."""
        return parse_identifiers(self.citing)

    @property
    def cited_identifiers(self) -> list[ParsedIdentifier]:
        """The identifiers of the cited entity, parsed from ``cited``."""
        return parse_identifiers(self.cited)


__all__ = ["Citation"]
