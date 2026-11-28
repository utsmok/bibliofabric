"""Clients for the Wikibase REST entity routes (items and properties)."""

from bibliofabric import BaseApiClient
from bibliofabric.exceptions import ConfigurationError

from ..dialect import REST_PREFIX
from ..ids import normalize_wikidata_id
from ..models import RestItem, RestProperty, RestSitelink, RestTermResponse


def _entity_segment(id: str) -> tuple[str, str]:
    """Return the REST segment for an entity id (``items`` or ``properties``)."""
    normalized = normalize_wikidata_id(id)
    kind = normalized[0]
    if kind == "Q":
        return "items", normalized
    if kind == "P":
        return "properties", normalized
    raise ConfigurationError(
        f"The REST entity routes serve items and properties; {normalized!r} "
        "must be fetched through the Action API (wbgetentities)."
    )


class ItemsClient:
    """Client for the REST item routes under ``/entities/items``.

    The REST payload differs from ``wbgetentities``: labels and descriptions
    are language-to-string maps, aliases are language-to-list-of-strings
    maps, and each term route answers one language with a fallback chain.
    """

    def __init__(self, client: BaseApiClient) -> None:
        """Build the resource client on a ``QuidditaClient``."""
        self._client = client

    async def get(self, id: str) -> RestItem:
        """Return the full REST item for ``id``.

        The ``_fields`` parameter the OpenAPI document lists is rejected by
        the live API with ``invalid-query-parameter`` (verified on
        2026-11-27), so full payloads are the only option.
        """
        segment, normalized = _entity_segment(id)
        response = await self._client.request(
            "GET", f"{REST_PREFIX}/entities/{segment}/{normalized}"
        )
        return RestItem.model_validate(self._client.parse_json(response))

    async def _term(self, id: str, part: str, language: str) -> RestTermResponse:
        segment, normalized = _entity_segment(id)
        # The fallback routes answer 307 when another language serves the
        # term (verified 2026-11-27), so this request follows redirects.
        response = await self._client.request(
            "GET",
            f"{REST_PREFIX}/entities/{segment}/{normalized}/{part}/{language}",
            follow_redirects=True,
        )
        body = self._client.parse_json(response)
        if isinstance(body, str):
            # The fallback target answers the plain value string.
            body = {"language": language, "value": body}
        return RestTermResponse.model_validate(body)

    async def label(self, id: str, language: str) -> RestTermResponse:
        """Return the item label in ``language`` (no fallback chain)."""
        return await self._term(id, "labels", language)

    async def label_with_fallback(self, id: str, language: str) -> str:
        """Return the item label in ``language`` or a fallback language.

        The fallback route answers 307 and the redirect target answers the
        plain value string, so this method returns ``str``.
        """
        return await self._term_value(id, "labels_with_language_fallback", language)

    async def description(self, id: str, language: str) -> RestTermResponse:
        """Return the item description in ``language`` (no fallback chain)."""
        return await self._term(id, "descriptions", language)

    async def description_with_fallback(self, id: str, language: str) -> str:
        """Return the item description in ``language`` or a fallback language."""
        return await self._term_value(
            id, "descriptions_with_language_fallback", language
        )

    async def _term_value(self, id: str, part: str, language: str) -> str:
        term = await self._term(id, part, language)
        return term.value

    async def sitelink(self, id: str, site: str) -> RestSitelink:
        """Return one site link of an item."""
        segment, normalized = _entity_segment(id)
        if segment != "items":
            raise ConfigurationError("Site links exist on items only.")
        response = await self._client.request(
            "GET", f"{REST_PREFIX}/entities/{segment}/{normalized}/sitelinks/{site}"
        )
        return RestSitelink.model_validate(self._client.parse_json(response))


class PropertiesClient:
    """Client for the REST property routes under ``/entities/properties``."""

    def __init__(self, client: BaseApiClient) -> None:
        """Build the resource client on a ``QuidditaClient``."""
        self._client = client

    async def get(self, id: str) -> RestProperty:
        """Return the full REST property for ``id``."""
        segment, normalized = _entity_segment(id)
        response = await self._client.request(
            "GET", f"{REST_PREFIX}/entities/{segment}/{normalized}"
        )
        return RestProperty.model_validate(self._client.parse_json(response))

    async def datatypes(self) -> dict[str, str]:
        """Return ``/property-data-types``: data type id to value type id."""
        response = await self._client.request(
            "GET", f"{REST_PREFIX}/property-data-types"
        )
        body = self._client.parse_json(response)
        return {
            key: value
            for key, value in body.items()
            if isinstance(key, str) and isinstance(value, str)
        }


__all__ = ["ItemsClient", "PropertiesClient"]
