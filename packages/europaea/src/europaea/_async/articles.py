"""Clients for the per-article Europe PMC routes."""

import re
from collections.abc import Mapping
from typing import Any, override

from bibliofabric.exceptions import ConfigurationError, NotFoundError
from bibliofabric.paging import Page
from pydantic import BaseModel

from ..models import (
    Citation,
    DatabaseLink,
    DataLinksResponse,
    EvaluationsResponse,
    LabsLinksResponse,
    SearchResult,
    StatusUpdateResponse,
    XmlDocument,
)
from .resources import EUROPEPMC_LIST_DIALECT, EuropepmcResourceClient


def split_article_id(id: str) -> tuple[str, str]:
    """Split ``"MED:23903748"`` or ``"MED/23903748"`` into source and id.

    Raises:
        ConfigurationError: when the id carries no source part. Europe PMC
            answers a source-less id only through the search route.
    """
    text = str(id)
    if ":" in text:
        source, _, bare = text.partition(":")
    elif "/" in text:
        source, _, bare = text.partition("/")
    else:
        raise ConfigurationError(
            f"Europe PMC article ids must look like 'MED:23903748', got {text!r}."
        )
    source = source.strip().upper()
    if not source or not bare.strip():
        raise ConfigurationError(
            f"Europe PMC article ids must look like 'MED:23903748', got {text!r}."
        )
    return source, bare.strip()


class ArticlesClient(EuropepmcResourceClient[SearchResult]):
    """Client for the article routes: ``/article/{source}/{id}`` and friends.

    ``get("MED:23903748")`` returns the ``resultType=core`` record. The
    sibling routes (references, citations, database links, XML full text,
    and more) hang off the same resource as named methods; the list routes
    reuse the framework paging support.
    """

    path = "article"
    model = SearchResult
    batch_size = 0

    @override
    def item_path(self, id: str | int) -> str:
        """Return ``article/{source}/{id}`` for a combined article id."""
        source, bare = split_article_id(str(id))
        return f"{self.path}/{source}/{bare}"

    @override
    async def get(
        self,
        id: str | int,
        *,
        params: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> SearchResult:
        """Fetch one article record as ``resultType=core``."""
        merged: dict[str, Any] = {"format": "json", "resultType": "core"}
        if params:
            merged.update(params)
        return await super().get(id, params=merged, **kwargs)

    async def full_text_xml(self, id: str) -> XmlDocument:
        """Return the JATS full text of an open access article as text.

        ``id`` is a bare Europe PMC id such as ``PMC13810549`` (a PMCID),
        a PMID, or an NBK accession. The route answers 404 for articles
        without open access full text.
        """
        return await self._fetch_xml(f"{id}/fullTextXML")

    async def book_xml(self, id: str) -> XmlDocument:
        """Return the book XML of an open access bookshelf entry.

        ``id`` is the Europe PMC NBK accession (for example ``NBK32884``) or
        the book's metadata PMID. For a valid id without open access XML the
        API answers HTTP 200 with a wrapper document that carries a message;
        the wrapper fields land on :attr:`XmlDocument.message` and
        :attr:`XmlDocument.is_open_access`.
        """
        return await self._fetch_xml(f"{id}/bookXML")

    async def supplementary_files(
        self, id: str, *, include_inline_image: bool = False
    ) -> bytes:
        """Return the supplementary files bundle of an article (a ZIP archive).

        ``id`` is a bare Europe PMC id such as ``PMC13810549``. Pass
        ``include_inline_image=True`` to also include the inline images of
        the article.
        """
        params: dict[str, str] = (
            {"includeInlineImage": "true"} if include_inline_image else {}
        )
        response = await self._client.request(
            "GET",
            f"{id}/supplementaryFiles",
            params=params or None,
            headers={"Accept": "application/octet-stream"},
        )
        return response.content

    async def references(
        self, id: str, *, page: int | None = None, page_size: int | None = None
    ) -> Page[Citation]:
        """Fetch one page of the reference list of an article.

        Paging uses ``page`` and ``pageSize``; ``total`` is the reference
        count of the article.
        """
        client = _ArticleListClient(self, str(id), "references", model=Citation)
        return await client.search(page=page, page_size=page_size)

    async def citations(
        self, id: str, *, page: int | None = None, page_size: int | None = None
    ) -> Page[Citation]:
        """Fetch one page of the citation list (citing articles) of an article."""
        client = _ArticleListClient(self, str(id), "citations", model=Citation)
        return await client.search(page=page, page_size=page_size)

    async def database_links(
        self, id: str, *, page: int | None = None, page_size: int | None = None
    ) -> Page[DatabaseLink]:
        """Fetch one page of the curated database cross-references of an article."""
        client = _ArticleListClient(self, str(id), "databaseLinks", model=DatabaseLink)
        return await client.search(page=page, page_size=page_size)

    async def data_links(
        self,
        id: str,
        *,
        category: str | None = None,
        obtained_by: str | None = None,
    ) -> DataLinksResponse:
        """Return the data links of an article (not paged, one envelope).

        ``category`` selects a data link category (for example ``ALT`` for
        Altmetric); ``obtained_by`` filters on the link source.
        """
        source, bare = split_article_id(str(id))
        params: dict[str, str] = {"format": "json"}
        if category:
            params["category"] = category
        if obtained_by:
            params["obtainedBy"] = obtained_by
        body = await self._client.get_json(f"{source}/{bare}/datalinks", params=params)
        return DataLinksResponse.model_validate(body)

    async def labs_links(
        self, id: str, *, page: int | None = None, page_size: int | None = None
    ) -> LabsLinksResponse:
        """Return the per-provider link counts of an article.

        Paging applies to the provider list; ``providerIds`` accepts a list
        of provider identifiers when callers need a subset.
        """
        source, bare = split_article_id(str(id))
        params: dict[str, str] = {"format": "json"}
        if page is not None:
            params["page"] = str(page)
        if page_size is not None:
            params["pageSize"] = str(page_size)
        body = await self._client.get_json(f"{source}/{bare}/labsLinks", params=params)
        return LabsLinksResponse.model_validate(body)

    async def status_updates(
        self, ids: str | list[str], *, source: str | None = None
    ) -> StatusUpdateResponse:
        """Return the status updates of articles (the status monitor).

        This is the ``POST /status-update-search`` route: it reports the
        publication status changes Europe PMC recorded for the queried
        articles (for example preprints that received a published version).
        It is a read-only POST, so the request is retried.

        Args:
            ids: One article id or a list of them. Combined ids use the
                ``SOURCE:ID`` form (``"MED:23903748"``); bare ids such as
                ``"PPR324115"`` take ``source`` as their source code.
            source: Source code for bare external ids (``PPR``, ``PMC``,
                ``MED``); required when ``ids`` carries a bare id.
        """
        inputs: list[dict[str, str]] = []
        for entry in [ids] if isinstance(ids, str) else list(ids):
            text = str(entry)
            if ":" in text or "/" in text:
                source_code, bare = split_article_id(text)
                inputs.append({"src": source_code, "extId": bare})
            elif source:
                inputs.append({"src": source.upper(), "extId": text})
            else:
                raise ConfigurationError(
                    f"Bare external id {text!r} needs a source= value "
                    "(for example source='PPR')."
                )
        response = await self._client.request(
            "POST",
            "status-update-search",
            params={"format": "json"},
            json={"ids": inputs},
            headers={"Content-Type": "application/json"},
            retry=True,
        )
        parsed = self._client.parse_json(response)
        return StatusUpdateResponse.model_validate(parsed)

    async def evaluations(self, id: str) -> EvaluationsResponse:
        """Return the community evaluations (peer reviews) of an article."""
        source, bare = split_article_id(str(id))
        body = await self._client.get_json(
            f"evaluations/{source}/{bare}", params={"format": "json"}
        )
        return EvaluationsResponse.model_validate(body)

    async def exists(self, id: str | int) -> bool:
        """Return ``True`` when the article exists; 404 returns ``False``.

        Uses ``GET`` because the Europe PMC gateway answers ``HEAD`` with 405.
        """
        try:
            await self.get(id)
        except NotFoundError:
            return False
        return True

    async def _fetch_xml(self, path: str) -> XmlDocument:
        """Fetch an XML route and wrap the document text with its extras."""
        response = await self._client.request(
            "GET", path, headers={"Accept": "application/xml"}
        )
        text = response.text
        if "<message>" in text:
            document = _parse_xml_wrapper(text)
            if document.message and "not" in document.message:
                raise NotFoundError(
                    f"Europe PMC answered no document for {path}: {document.message}",
                    response=response,
                )
            return document
        return XmlDocument(xml=text)


def _parse_xml_wrapper(text: str) -> XmlDocument:
    """Parse the small wrapper document the XML routes answer for misses.

    The wrapper is a namespace-heavy document (for example
    ``<ns4:fullTextXMLBean ...><fullTextXML><pmId>...</pmId>
    <message>...</message><isOpenAccess>N</isOpenAccess></fullTextXML>``,
    sometimes without the namespace declarations), so the two route extras
    are extracted with plain element matches instead of an XML parser.
    """
    document = XmlDocument(xml=text)
    message = _MESSAGE_RE.search(text)
    open_access = _OPEN_ACCESS_RE.search(text)
    if message is not None:
        document.message = message.group(1).strip()
    if open_access is not None:
        document.is_open_access = open_access.group(1).strip()
    return document


_MESSAGE_RE = re.compile(r"<message>(.*?)</message>", re.DOTALL)
_OPEN_ACCESS_RE = re.compile(r"<isOpenAccess>(.*?)</isOpenAccess>", re.DOTALL)


class _ArticleListClient(EuropepmcResourceClient[Any]):
    """Internal list client bound to one article sub-route."""

    def __init__(
        self,
        owner: ArticlesClient,
        id: str,
        sub_path: str,
        *,
        model: type[BaseModel],
    ) -> None:
        source, bare = split_article_id(str(id))
        super().__init__(
            owner._client,
            path=f"{source}/{bare}/{sub_path}",
            dialect=EUROPEPMC_LIST_DIALECT,
        )
        self.model = model


__all__ = ["ArticlesClient", "split_article_id"]
