"""Typed vocabulary of OpenAIRE Graph relation types and their inverses.

The table mirrors the ``/v3/research-products/links/relations-info`` payload
(trimmed real copy: ``tests/fixtures/relations_info.json``). Linkage studies
constantly need the opposite direction of a relation, so the inverse pairs
are static data instead of a live lookup.
"""

from typing import Final, Literal

RelationName = Literal[
    "Cites",
    "IsCitedBy",
    "IsSourceOf",
    "IsDerivedFrom",
    "IsRelatedTo",
    "HasAmongTopNSimilarDocuments",
    "IsAmongTopNSimilarDocuments",
    "References",
    "IsReferencedBy",
    "HasPart",
    "IsPartOf",
    "IsSupplementTo",
    "IsSupplementedBy",
    "IsNewVersionOf",
    "IsPreviousVersionOf",
    "HasVersion",
    "IsVersionOf",
    "Continues",
    "IsContinuedBy",
    "Documents",
    "IsDocumentedBy",
    "IsIdenticalTo",
    "IsOriginalFormOf",
    "IsVariantFormOf",
    "Reviews",
    "IsReviewedBy",
    "Compiles",
    "IsCompiledBy",
    "Obsoletes",
    "IsObsoletedBy",
    "Describes",
    "IsDescribedBy",
    "Requires",
    "IsRequiredBy",
    "IsMetadataOf",
    "IsMetadataFor",
]
"""Every relation name the links endpoint can produce (both directions)."""

RELATION_INVERSES: Final[dict[str, str]] = {
    "Cites": "IsCitedBy",
    "IsCitedBy": "Cites",
    "IsSourceOf": "IsDerivedFrom",
    "IsDerivedFrom": "IsSourceOf",
    "IsRelatedTo": "IsRelatedTo",
    "HasAmongTopNSimilarDocuments": "IsAmongTopNSimilarDocuments",
    "IsAmongTopNSimilarDocuments": "HasAmongTopNSimilarDocuments",
    "References": "IsReferencedBy",
    "IsReferencedBy": "References",
    "HasPart": "IsPartOf",
    "IsPartOf": "HasPart",
    "IsSupplementTo": "IsSupplementedBy",
    "IsSupplementedBy": "IsSupplementTo",
    "IsNewVersionOf": "IsPreviousVersionOf",
    "IsPreviousVersionOf": "IsNewVersionOf",
    "HasVersion": "IsVersionOf",
    "IsVersionOf": "HasVersion",
    "Continues": "IsContinuedBy",
    "IsContinuedBy": "Continues",
    "Documents": "IsDocumentedBy",
    "IsDocumentedBy": "Documents",
    "IsIdenticalTo": "IsIdenticalTo",
    "IsOriginalFormOf": "IsVariantFormOf",
    "IsVariantFormOf": "IsOriginalFormOf",
    "Reviews": "IsReviewedBy",
    "IsReviewedBy": "Reviews",
    "Compiles": "IsCompiledBy",
    "IsCompiledBy": "Compiles",
    "Obsoletes": "IsObsoletedBy",
    "IsObsoletedBy": "Obsoletes",
    "Describes": "IsDescribedBy",
    "IsDescribedBy": "Describes",
    "Requires": "IsRequiredBy",
    "IsRequiredBy": "Requires",
    "IsMetadataOf": "IsMetadataFor",
    "IsMetadataFor": "IsMetadataOf",
}
"""Inverse relation for every :data:`RelationName`; symmetric names map to
themselves (``IsRelatedTo``, ``IsIdenticalTo``)."""

__all__ = ["RELATION_INVERSES", "RelationName", "relation_inverse"]


def relation_inverse(name: str) -> str | None:
    """Return the inverse relation of ``name`` (``Cites`` -> ``IsCitedBy``).

    Symmetric relations return the name itself; unknown names return
    ``None``.
    """
    return RELATION_INVERSES.get(name)
