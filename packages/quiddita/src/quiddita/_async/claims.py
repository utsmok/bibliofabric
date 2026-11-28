"""Client for ``wbgetclaims``."""

from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError

from ..dialect import ACTION_PATH
from ..ids import normalize_wikidata_id
from ..models import Claim, ClaimsByProperty

_VALID_RANKS = frozenset({"deprecated", "normal", "preferred"})


class ClaimsClient:
    """Client for the claims of one entity via ``wbgetclaims``.

    For full entity payloads with claims included, prefer
    :attr:`QuidditaClient.entities`; ``wbgetclaims`` filters the claims of
    one entity by property and rank.
    """

    def __init__(self, client: BaseApiClient) -> None:
        """Build the resource client on a ``QuidditaClient``."""
        self._client = client

    async def get(
        self,
        id: str,
        *,
        property: str | None = None,
        rank: str | None = None,
    ) -> ClaimsByProperty:
        """Return the claims of ``id``, keyed by property id.

        Args:
            id: Entity id (``Q42``) or a URL form.
            property: Restrict to one property (``P18``).
            rank: ``"deprecated"``, ``"normal"``, or ``"preferred"``. Any
                other value makes the API answer ``badvalue`` (verified on
                2026-11-27), so the client rejects it first.

        Returns:
            A dict of property id to the :class:`~quiddita.Claim`
            records. An entity without claims answers ``{}``.
        """
        if rank is not None and rank not in _VALID_RANKS:
            raise ConfigurationError(
                f"rank must be one of {sorted(_VALID_RANKS)}, got {rank!r}."
            )
        request_params: dict[str, str] = {
            "action": "wbgetclaims",
            "format": "json",
            "entity": normalize_wikidata_id(id),
        }
        if property is not None:
            request_params["property"] = normalize_wikidata_id(property)
        if rank is not None:
            request_params["rank"] = rank
        response = await self._client.request("GET", ACTION_PATH, params=request_params)
        body = self._client.parse_json(response)
        self._client.unwrapper.results(body)  # raises on soft errors
        claims = body.get("claims") if isinstance(body, dict) else None
        if not isinstance(claims, dict):
            return {}
        result: ClaimsByProperty = {}
        for property_id, records in claims.items():
            if not isinstance(records, list):
                continue
            result[property_id] = [
                validate_model(Claim, record)
                for record in records
                if isinstance(record, dict)
            ]
        return result


__all__ = ["ClaimsClient"]
