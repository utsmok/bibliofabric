"""Client for the Zenodo vocabularies endpoints."""

from collections.abc import AsyncIterator, Mapping
from typing import Any
from urllib.parse import quote

from bibliofabric import BaseApiClient, Page, ValidationError
from bibliofabric.exceptions import ConfigurationError
from pydantic import ValidationError as PydanticValidationError

from ..models import ZenothecaVocabulary


class VocabulariesClient:
    """Client for the ``/vocabularies`` endpoints.

    A vocabulary is a small reference list (``resourcetypes``,
    ``licenses``, ``languages``, ``communitytypes``); ``funders`` and
    ``affiliations`` exist but answer no entries yet, and unknown names
    answer 404. Entries page like a search (``size``, ``page``, ``q``,
    sorted by title).
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def search(
        self,
        name: str,
        *,
        query: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> Page[ZenothecaVocabulary]:
        """Fetch one page of the entries of vocabulary ``name``."""
        query_params = self._query_params(
            query=query, page=page, page_size=page_size, params=params
        )
        response = await self._client.request(
            "GET", self._vocab_path(name), params=query_params
        )
        body = self._client.parse_json(response)
        unwrapper = self._client.unwrapper
        return Page(
            results=self._entries(unwrapper.results(body), name),
            total=unwrapper.total(body),
            next_cursor=None,
            page=page if page is not None else 1,
            meta=unwrapper.meta(body),
        )

    def iterate(
        self,
        name: str,
        *,
        query: str | None = None,
        page_size: int | None = None,
        limit: int | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> AsyncIterator[ZenothecaVocabulary]:
        """Iterate over every entry of vocabulary ``name``; ``limit`` stops early."""
        return self._iterate(
            name,
            query=query,
            page_size=page_size,
            limit=limit,
            params=params,
        )

    async def get(self, name: str, id: str) -> ZenothecaVocabulary:
        """Return one entry of vocabulary ``name``; 404 raises ``NotFoundError``."""
        wanted = id.strip()
        if not wanted:
            raise ConfigurationError("id must be a non-empty string.")
        response = await self._client.request(
            "GET",
            f"{self._vocab_path(name)}/{quote(wanted, safe='')}",
        )
        body = self._client.parse_json(response)
        entry = self._client.unwrapper.item(body)
        try:
            return ZenothecaVocabulary.model_validate(entry)
        except PydanticValidationError as error:
            raise ValidationError(
                f"The vocabulary entry of {name!r} does not match the "
                f"expected schema: {error}",
                raw=entry,
                error=error,
                model_name="ZenothecaVocabulary",
            ) from error

    async def _iterate(
        self,
        name: str,
        *,
        query: str | None,
        page_size: int | None,
        limit: int | None,
        params: Mapping[str, Any] | None,
    ) -> AsyncIterator[ZenothecaVocabulary]:
        """Walk the pages of one vocabulary."""
        page = 1
        fetched = 0
        while True:
            got = await self.search(
                name,
                query=query,
                page=page,
                page_size=page_size,
                params=params,
            )
            index = 0
            while index < len(got.results):
                yield got.results[index]
                index += 1
                fetched += 1
                if limit is not None and fetched >= limit:
                    return
            if not got.results or (got.total is not None and fetched >= got.total):
                return
            page += 1

    def _entries(self, records: list[Any], name: str) -> list[ZenothecaVocabulary]:
        """Validate the entries of one page against the vocabulary model."""
        entries: list[ZenothecaVocabulary] = []
        for record in records:
            try:
                entries.append(ZenothecaVocabulary.model_validate(record))
            except PydanticValidationError as error:
                raise ValidationError(
                    f"The vocabulary {name!r} returned an entry that does "
                    f"not match the expected schema: {error}",
                    raw=record,
                    error=error,
                    model_name="ZenothecaVocabulary",
                ) from error
        return entries

    @staticmethod
    def _query_params(
        *,
        query: str | None,
        page: int | None,
        page_size: int | None,
        params: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Collect the query string of one vocabulary page request."""
        collected: dict[str, Any] = dict(params) if params else {}
        if query is not None:
            collected["q"] = query
        if page is not None:
            collected["page"] = page
        if page_size is not None:
            collected["size"] = page_size
        return collected

    @staticmethod
    def _vocab_path(name: str) -> str:
        wanted = name.strip()
        if not wanted or "/" in wanted:
            raise ConfigurationError(f"{name!r} is not a Zenodo vocabulary name.")
        return f"vocabularies/{quote(wanted, safe='')}"


__all__ = ["VocabulariesClient"]
