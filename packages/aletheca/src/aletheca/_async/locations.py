"""Client for the OpenAlex locations endpoint."""

from collections.abc import Sequence

from bibliofabric.ids import normalize_doi

from ..dialect import _OPENALEX_URL_PREFIX
from ..models import LocationRecord
from .dialect import DOI_FIELDS, OpenAlexResourceClient


class LocationsClient(OpenAlexResourceClient[LocationRecord]):
    """Client for the ``/locations`` endpoint.

    One row per copy of a work at one source (the per-copy index used for
    OA-copy hunting and repository-harvest audits). Rows are addressed by
    namespaced ids such as ``doi:10.7717/peerj.4375`` or
    ``pmh:oai:arXiv.org:1706.03762``; ``get``/``search``/``iterate`` behave
    like on the entity endpoints. A list request costs one credit.
    """

    path = "locations"
    model = LocationRecord

    def normalize_id(self, value: str) -> str:
        """Keep namespaced ids intact: the single route 404s on bare DOIs.

        Only URL and route prefixes are stripped; the ``doi:``/``pmh:``/
        ``pmid:`` namespace and the value's case stay as given.
        """
        text = value.strip()
        text = text.removeprefix(_OPENALEX_URL_PREFIX)
        return text.removeprefix(f"{self.path}/")

    def build_batch_params(self, field: str, values: Sequence[str]) -> dict[str, str]:
        """Build one ``batch_get`` chunk without rewriting ``id`` to ``openalex``."""
        chunk = list(values)
        if field in DOI_FIELDS:
            chunk = [normalize_doi(value) for value in chunk]
        return {"filter": f"{field}:{'|'.join(chunk)}"}

    def record_keys(self, entity: LocationRecord, field: str) -> list[str]:
        """Match location keys, normalizing DOIs when batching by ``doi``."""
        if field == "doi":
            values: list[str] = []
            if entity.doi is not None:
                values.append(normalize_doi(str(entity.doi)))
                values.append(self.normalize_id(str(entity.doi)))
            return list(dict.fromkeys(values))
        return super().record_keys(entity, field)
