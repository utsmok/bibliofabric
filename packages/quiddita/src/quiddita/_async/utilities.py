"""Client for the small Action API read modules.

These modules wrap ``wbavailablebadges``, ``wbformatentities``,
``wbformatvalue``, ``wbparsevalue``, ``wbsgetsuggestions`` (the property
suggester), and ``wbcheckconstraints``. Each method maps one module; the
parameter facts come from the live study of 2026-11-27/28 and are recorded
in ``docs/quiddita/upstream-quirks.md``.
"""

import json
from typing import Any

from bibliofabric import BaseApiClient
from bibliofabric.exceptions import ConfigurationError

from ..ids import normalize_wikidata_id
from ..models import (
    CheckedClaim,
    ConstraintChecksByProperty,
    ParsedValue,
    PropertySuggestion,
)

ACTION_PATH = "w/api.php"


class UtilitiesClient:
    """Client for the Action API utility read modules."""

    def __init__(self, client: BaseApiClient) -> None:
        """Build the resource client on a ``QuidditaClient``."""
        self._client = client

    async def _module(self, action: str, params: dict[str, Any]) -> Any:
        """Send one Action API module request and parse its JSON body."""
        response = await self._client.request(
            "GET",
            ACTION_PATH,
            params={"action": action, "format": "json", **params},
        )
        return self._client.parse_json(response)

    async def available_badges(self) -> list[str]:
        """Return every badge id usable on site links (``wbavailablebadges``)."""
        body = await self._module("wbavailablebadges", {})
        badges = body.get("badges") if isinstance(body, dict) else None
        return [str(badge) for badge in badges or []]

    async def format_entities(self, ids: list[str]) -> dict[str, str]:
        """Return HTML links per id (``wbformatentities``).

        The module ignores ``props`` and ``languages`` with a warning
        (verified 2026-11-27), so they are not offered here.
        """
        if not ids:
            raise ConfigurationError("format_entities requires at least one id.")
        normalized = [normalize_wikidata_id(entity_id) for entity_id in ids]
        body = await self._module("wbformatentities", {"ids": "|".join(normalized)})
        table = body.get("wbformatentities") if isinstance(body, dict) else None
        return {str(key): str(value) for key, value in (table or {}).items()}

    async def format_value(self, datavalue: dict[str, Any], datatype: str) -> str:
        """Return the HTML rendering of one datavalue (``wbformatvalue``).

        ``datavalue`` is the ``{"type": ..., "value": ...}`` shape; the
        service answers ``baddatavalue`` without the ``type`` key.
        """
        body = await self._module(
            "wbformatvalue",
            {"datavalue": json.dumps(datavalue), "datatype": datatype},
        )
        return str(body.get("result")) if isinstance(body, dict) else ""

    async def parse_value(
        self,
        values: list[str],
        *,
        datatype: str,
    ) -> list[ParsedValue]:
        """Parse serialized values against a datatype (``wbparsevalue``)."""
        if not values:
            raise ConfigurationError("parse_value requires at least one value.")
        body = await self._module(
            "wbparsevalue", {"values": "|".join(values), "datatype": datatype}
        )
        results = body.get("results") if isinstance(body, dict) else None
        return [ParsedValue.model_validate(item) for item in results or []]

    async def suggestions(
        self,
        *,
        entity: str | None = None,
        properties: list[str] | None = None,
        types: list[str] | None = None,
        language: str | None = None,
        limit: int | None = None,
        continuation: str | None = None,
    ) -> list[PropertySuggestion]:
        """Return property suggestions (``wbsgetsuggestions``).

        The module answers an error unless ``entity`` or ``properties`` is
        given (verified 2026-11-27), so neither being set raises
        ``ConfigurationError`` before a request is sent.
        """
        params: dict[str, Any] = {}
        if entity is not None:
            params["entity"] = normalize_wikidata_id(entity)
        if properties:
            params["properties"] = "|".join(properties)
        if types:
            params["types"] = "|".join(types)
        if language is not None:
            params["language"] = language
        if limit is not None:
            params["limit"] = str(limit)
        if continuation is not None:
            params["continue"] = continuation
        if entity is None and not properties:
            raise ConfigurationError(
                "suggestions requires entity= or properties=; the module "
                "answers propertysuggester-wbsgetsuggestions-either-entity-"
                "or-properties without both."
            )
        body = await self._module("wbsgetsuggestions", params)
        search = body.get("search") if isinstance(body, dict) else None
        return [PropertySuggestion.model_validate(item) for item in search or []]

    async def check_constraints(
        self,
        ids: list[str],
        *,
        claim_ids: list[str] | None = None,
        constraint_ids: list[str] | None = None,
        statuses: list[str] | None = None,
    ) -> dict[str, ConstraintChecksByProperty]:
        """Check constraint compliance of entities (``wbcheckconstraints``).

        The module's entity parameter is ``id`` (verified 2026-11-28);
        ``entity`` or ``entityid`` answer the ``no-data`` error. Each
        result carries the claim id, the constraint, and the check status
        per claim.
        """
        params: dict[str, Any] = {
            "id": "|".join(normalize_wikidata_id(entity_id) for entity_id in ids)
        }
        if claim_ids:
            params["claimid"] = "|".join(claim_ids)
        if constraint_ids:
            params["constraintid"] = "|".join(constraint_ids)
        if statuses:
            params["status"] = "|".join(statuses)
        body = await self._module("wbcheckconstraints", params)
        table = body.get("wbcheckconstraints") if isinstance(body, dict) else None
        report: dict[str, ConstraintChecksByProperty] = {}
        for entity_id, entity_report in (table or {}).items():
            claims = (
                entity_report.get("claims", {})
                if isinstance(entity_report, dict)
                else {}
            )
            report[str(entity_id)] = {
                str(property_id): [CheckedClaim.model_validate(item) for item in items]
                for property_id, items in claims.items()
            }
        return report


__all__ = ["UtilitiesClient"]
