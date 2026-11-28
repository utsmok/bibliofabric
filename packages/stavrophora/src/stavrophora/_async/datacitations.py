"""Data citations resource: the beta ``/beta/datacitations`` route.

The route lives beside the ``/v1`` API (``https://api.crossref.org/beta/
datacitations``), runs in its own ``datacitations`` pool (3 requests per
second, 3 concurrent on 2026-11-28), and pages by a 0-based ``page`` number:
``message.next-page`` holds the next page number, or ``null`` after the last
page. Crossref marks the route as beta, so its contents and output format
may change.
"""

from collections.abc import AsyncIterator
from typing import Any

import httpx
from bibliofabric import BaseApiClient, Page, validate_model
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import normalize_doi

from ..models import DataCitation

#: Path of the route, relative to the API origin (not to ``/v1``).
DATACITATIONS_PATH = "/beta/datacitations"

#: Largest ``rows`` value the route accepts; above it the route answers 400.
DATACITATIONS_MAX_ROWS = 1000


class DataCitationsResource:
    """Typed client for the Crossref Data Citations API (beta).

    Every filter is optional and the filters combine with AND:
    ``subject_id`` (DOI of the citing work), ``object_id`` (DOI of the cited
    dataset or software), ``member_id`` (Crossref member of the citing
    work), ``relation`` (for example ``references``), and
    ``from_created_date`` / ``until_created_date`` (when Crossref added the
    relationship; ``2025``, ``2025-01``, ``2025-01-01``, or
    ``2025-01-01T12:00``).
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client
        self._url = str(httpx.URL(client.base_url).copy_with(path=DATACITATIONS_PATH))

    async def search(
        self,
        *,
        subject_id: str | None = None,
        object_id: str | None = None,
        member_id: str | int | None = None,
        relation: str | None = None,
        from_created_date: str | None = None,
        until_created_date: str | None = None,
        rows: int | None = None,
        page: int | None = None,
    ) -> Page[DataCitation]:
        """Return one page of data citations.

        ``page`` is 0-based. ``page.next_cursor`` holds the next page number
        as a string, or ``None`` after the last page; ``page.total`` is the
        number of matching relationships.
        """
        params = _params(
            subject_id=subject_id,
            object_id=object_id,
            member_id=member_id,
            relation=relation,
            from_created_date=from_created_date,
            until_created_date=until_created_date,
            rows=rows,
            page=page,
        )
        message, response = await self._fetch(params)
        results = [
            validate_model(
                DataCitation, item, request=response.request, response=response
            )
            for item in message.get("items") or []
        ]
        next_page = message.get("next-page")
        total = message.get("total-results")
        meta = {key: value for key, value in message.items() if key != "items"}
        return Page(
            results=results,
            total=int(total) if total is not None else None,
            next_cursor=str(next_page) if next_page is not None else None,
            page=page if page is not None else 0,
            meta=meta,
        )

    async def iterate(
        self,
        *,
        subject_id: str | None = None,
        object_id: str | None = None,
        member_id: str | int | None = None,
        relation: str | None = None,
        from_created_date: str | None = None,
        until_created_date: str | None = None,
        rows: int = DATACITATIONS_MAX_ROWS,
    ) -> AsyncIterator[DataCitation]:
        """Yield every matching data citation, following ``next-page``."""
        page_number: Any = 0
        while page_number is not None:
            params = _params(
                subject_id=subject_id,
                object_id=object_id,
                member_id=member_id,
                relation=relation,
                from_created_date=from_created_date,
                until_created_date=until_created_date,
                rows=rows,
                page=int(page_number),
            )
            message, response = await self._fetch(params)
            items = message.get("items") or []
            for item in items:
                yield validate_model(
                    DataCitation, item, request=response.request, response=response
                )
            page_number = message.get("next-page") if items else None

    async def _fetch(
        self, params: dict[str, Any]
    ) -> tuple[dict[str, Any], httpx.Response]:
        """Send one request and return the ``message`` object and the response."""
        response = await self._client.request("GET", self._url, params=params)
        body = self._client.parse_json(response)
        message = body.get("message") if isinstance(body, dict) else None
        if not isinstance(message, dict):
            raise ConfigurationError(
                "Crossref /beta/datacitations answered without a message object."
            )
        return message, response

    async def count(
        self,
        *,
        subject_id: str | None = None,
        object_id: str | None = None,
        member_id: str | int | None = None,
        relation: str | None = None,
        from_created_date: str | None = None,
        until_created_date: str | None = None,
    ) -> int:
        """Return the number of matching data citations (one 1-row request)."""
        page = await self.search(
            subject_id=subject_id,
            object_id=object_id,
            member_id=member_id,
            relation=relation,
            from_created_date=from_created_date,
            until_created_date=until_created_date,
            rows=1,
        )
        return page.total or 0


def _params(
    *,
    subject_id: str | None,
    object_id: str | None,
    member_id: str | int | None,
    relation: str | None,
    from_created_date: str | None,
    until_created_date: str | None,
    rows: int | None,
    page: int | None,
) -> dict[str, Any]:
    """Build and check the query parameters of one request."""
    if rows is not None and not 1 <= rows <= DATACITATIONS_MAX_ROWS:
        raise ConfigurationError(
            f"rows must be between 1 and {DATACITATIONS_MAX_ROWS}, got {rows}."
        )
    if page is not None and page < 0:
        raise ConfigurationError(f"page is 0-based and must be >= 0, got {page}.")
    candidates: dict[str, Any] = {
        "subject-id": normalize_doi(subject_id) if subject_id else None,
        "object-id": normalize_doi(object_id) if object_id else None,
        "member-id": str(member_id) if member_id is not None else None,
        "relation": relation,
        "from-created-date": from_created_date,
        "until-created-date": until_created_date,
        "rows": rows,
        "page": page,
    }
    return {key: value for key, value in candidates.items() if value is not None}


__all__ = ["DATACITATIONS_MAX_ROWS", "DATACITATIONS_PATH", "DataCitationsResource"]
