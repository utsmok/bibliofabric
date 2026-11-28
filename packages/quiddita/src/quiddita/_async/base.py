"""Base shared by the Wikidata resources."""

from typing import Any, override

from bibliofabric import ResourceClient
from pydantic import BaseModel

from ..dialect import WIKIDATA_DIALECT
from ..ids import normalize_wikidata_id


class WikidataResourceClient[E: BaseModel](ResourceClient[E]):
    """Base client for Action API resources: dialect and id normalization."""

    path = "w/api.php"
    dialect = WIKIDATA_DIALECT

    @override
    def normalize_id(self, value: str) -> str:
        """Return the bare canonical id (``Q42``, ``P31``, ``L1``)."""
        return normalize_wikidata_id(value)


def join_values(values: Any) -> Any:
    """Join a sequence for MediaWiki multi-value parameters (``|``)."""
    if values is None:
        return None
    if isinstance(values, str):
        return values
    return "|".join(values)


__all__ = ["WikidataResourceClient", "join_values"]
