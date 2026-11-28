"""Resource clients for the OpenCitations Index API v2 and Meta API v1.

Both APIs are unpaged: every operation answers with the complete result of
the query. Every operation accepts the row-shaping parameters ``require``,
``filter``, ``sort``, and ``format`` that the RAMOSE engine applies in that
order; ``format="csv"`` parses into the same models as the JSON form
because the CSV header repeats the JSON field names. Each dataset also has
a SPARQL endpoint, reached with ``sparql()`` and ``sparql_text()``.
"""

from collections.abc import Sequence
from typing import Any, Literal
from urllib.parse import urlencode

import httpx
from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError
from pydantic import BaseModel

from ..csvparse import parse_csv_rows
from ..dialect import (
    FORMATS,
    INDEX_API_PATH,
    INDEX_SPARQL_URL,
    META_API_PATH,
    META_SPARQL_URL,
)
from ..ids import (
    normalize_index_id,
    normalize_issn,
    normalize_meta_ids,
    normalize_oci,
    normalize_person_id,
)
from ..models import Citation, Count, MetadataRecord, SparqlResult

#: Result representation of an operation; ``format=csv`` overrides the
#: ``Accept`` header server-side.
RowFormat = Literal["json", "csv"]

#: Result representations of the SPARQL endpoints, selected through the
#: ``Accept`` header (verified 2026-11-28).
SPARQL_MEDIA_TYPES: dict[str, str] = {
    "json": "application/sparql-results+json",
    "xml": "application/sparql-results+xml",
    "csv": "text/csv",
    "tsv": "text/tab-separated-values",
    "turtle": "text/turtle",
    "n-triples": "application/n-triples",
}

#: How a SPARQL query travels: in the URL (``GET``) or in a form body
#: without a length limit (``POST``).
SparqlMethod = Literal["GET", "POST"]

#: The two orders the ``sort`` parameter accepts.
_SORT_ORDERS = ("asc", "desc")


def _row_params(
    *,
    require: str | Sequence[str] | None,
    filter: str | Sequence[str] | None,
    sort: str | None,
    format: RowFormat,
) -> list[tuple[str, str]]:
    """Build the query parameters one row operation sends.

    ``require`` and ``filter`` may repeat, so the parameters travel as a
    list of pairs instead of a dict. ``format`` always travels explicitly;
    it has priority over the ``Accept`` header. Names follow the API, hence
    the shadowing of the built-ins ``filter`` and ``format``.
    """
    if format not in FORMATS:
        raise ConfigurationError(
            f"OpenCitations format must be one of {sorted(FORMATS)}, got {format!r}."
        )
    pairs: list[tuple[str, str]] = []
    for key, values in (("require", require), ("filter", filter)):
        if values is None:
            continue
        for value in [values] if isinstance(values, str) else values:
            text = value.strip()
            if not text:
                raise ConfigurationError(
                    f"OpenCitations {key} entries must be non-empty, got {value!r}."
                )
            pairs.append((key, text))
    if sort is not None:
        text = sort.strip()
        order, separator, field = text.partition("(")
        field = field.removesuffix(")")
        if separator != "(" or order not in _SORT_ORDERS or not field.isidentifier():
            raise ConfigurationError(
                f"OpenCitations sort must look like 'asc(creation)' or "
                f"'desc(creation)', got {sort!r}."
            )
        pairs.append(("sort", text))
    pairs.append(("format", format))
    return pairs


def _attached_request(response: httpx.Response) -> httpx.Request | None:
    """Return the request of ``response``, or ``None`` when none is attached."""
    return getattr(response, "request", None)


async def _fetch_rows[E: BaseModel](
    client: BaseApiClient,
    model: type[E],
    path: str,
    params: list[tuple[str, str]] | None,
) -> list[E]:
    """Send one row request and validate every returned row.

    Repeated parameters travel in the query string of the path, which is
    the only way to send ``require=a&require=b``. JSON answers are read
    from the top-level list; CSV answers are parsed row by row into the
    same model. A JSON body that is not a list raises
    :class:`ConfigurationError`, because both APIs always answer lists.
    """
    if params:
        path = f"{path}?{urlencode(params)}"
    response = await client.request("GET", path)
    if response.headers.get("content-type", "").startswith("text/csv"):
        rows: list[Any] = parse_csv_rows(response.text)
    else:
        body = client.parse_json(response)
        if not isinstance(body, list):
            raise ConfigurationError(
                f"OpenCitations answered {type(body).__name__} instead of a list "
                f"for {path}."
            )
        rows = body
    return [
        validate_model(
            model, row, request=_attached_request(response), response=response
        )
        for row in rows
    ]


async def _fetch_count(client: BaseApiClient, path: str) -> int | None:
    """Send one count request and return the count, or ``None`` for ``[]``.

    An empty list is read as "no count reported". Any other body that is
    not a list raises :class:`ConfigurationError`, because the count
    operations always answer a list.
    """
    response = await client.request("GET", path)
    body = client.parse_json(response)
    if not isinstance(body, list):
        raise ConfigurationError(
            f"OpenCitations answered {type(body).__name__} instead of a list "
            f"for {path}."
        )
    if not body:
        return None
    return validate_model(
        Count, body[0], request=_attached_request(response), response=response
    ).count


async def _send_sparql(
    client: BaseApiClient,
    endpoint: str,
    query: str,
    *,
    method: SparqlMethod,
    accept: str,
    timeout: float | None,
) -> httpx.Response:
    """Send one SPARQL request to ``endpoint``, an absolute URL on a second host.

    The endpoints answer XML unless asked otherwise, so ``accept`` always
    travels. ``POST`` carries the query in a form body, which has no length
    limit; the request only reads, so it passes ``retry=True``.
    """
    if not query.strip():
        raise ConfigurationError("The SPARQL query must be non-empty.")
    headers = {"Accept": accept}
    if method == "POST":
        return await client.request(
            "POST",
            endpoint,
            data={"query": query},
            headers=headers,
            timeout=timeout,
            retry=True,
        )
    return await client.request(
        "GET", endpoint, params={"query": query}, headers=headers, timeout=timeout
    )


async def _run_sparql(
    client: BaseApiClient,
    endpoint: str,
    query: str,
    *,
    method: SparqlMethod,
    timeout: float | None,
) -> SparqlResult:
    """Run a SPARQL query and validate the SPARQL 1.1 JSON answer."""
    response = await _send_sparql(
        client,
        endpoint,
        query,
        method=method,
        accept=SPARQL_MEDIA_TYPES["json"],
        timeout=timeout,
    )
    return validate_model(
        SparqlResult,
        client.parse_json(response),
        request=_attached_request(response),
        response=response,
    )


async def _run_sparql_text(
    client: BaseApiClient,
    endpoint: str,
    query: str,
    *,
    format: str,
    method: SparqlMethod,
    timeout: float | None,
) -> str:
    """Run a SPARQL query and return the raw body of the requested representation."""
    accept = SPARQL_MEDIA_TYPES.get(format)
    if accept is None:
        raise ConfigurationError(
            "SPARQL format must be one of "
            f"{sorted(SPARQL_MEDIA_TYPES)}, got {format!r}."
        )
    response = await _send_sparql(
        client, endpoint, query, method=method, accept=accept, timeout=timeout
    )
    return response.text


class IndexClient:
    """The read operations of the OpenCitations Index API v2.

    Every operation sends one GET and returns the complete result; the API
    has no paging. ``citations`` and ``references`` accept ``require``,
    ``filter``, ``sort``, and ``format``; ``filter`` entries look like
    ``creation:>2019-12`` (a regular expression, or ``=``, ``<``, ``>``
    with a value), and ``sort`` looks like ``desc(creation)``. The SPARQL
    endpoint of the Index dataset answers arbitrary queries through
    :meth:`sparql` and :meth:`sparql_text`.
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def citations(
        self,
        id: str,
        *,
        require: str | Sequence[str] | None = None,
        filter: str | Sequence[str] | None = None,
        sort: str | None = None,
        format: RowFormat = "json",
    ) -> list[Citation]:
        """Return the incoming citations of one entity.

        Every row records a reference in which ``cited`` identifies the
        entity. ``id`` is a prefixed identifier (``doi:``, ``omid:``,
        ``pmid:``, ``issn:``, or ``isbn:``); an unknown identifier answers
        with an empty list. ``require`` drops rows whose field is empty,
        ``filter`` keeps matching rows, ``sort`` orders them, and
        ``format="csv"`` asks the server for the CSV representation.
        """
        path = f"{INDEX_API_PATH}/citations/{normalize_index_id(id)}"
        params = _row_params(require=require, filter=filter, sort=sort, format=format)
        return await _fetch_rows(self._client, Citation, path, params)

    async def references(
        self,
        id: str,
        *,
        require: str | Sequence[str] | None = None,
        filter: str | Sequence[str] | None = None,
        sort: str | None = None,
        format: RowFormat = "json",
    ) -> list[Citation]:
        """Return the outgoing references of one entity.

        Every row records a reference of the reference list in which
        ``citing`` identifies the entity. The parameters behave exactly as
        in :meth:`citations`.
        """
        path = f"{INDEX_API_PATH}/references/{normalize_index_id(id)}"
        params = _row_params(require=require, filter=filter, sort=sort, format=format)
        return await _fetch_rows(self._client, Citation, path, params)

    async def citation(self, oci: str) -> Citation | None:
        """Return the one citation with this Open Citation Identifier.

        ``oci`` is the two dash-separated numbers without the ``oci:``
        prefix (``06101801781-06180334099``); a value with the prefix is
        accepted and stripped. Returns ``None`` when no citation carries
        the identifier.
        """
        path = f"{INDEX_API_PATH}/citation/{normalize_oci(oci)}"
        rows = await _fetch_rows(self._client, Citation, path, None)
        return rows[0] if rows else None

    async def citation_count(self, id: str) -> int | None:
        """Return the number of incoming citations of one entity.

        An unknown identifier answers ``0``: the API returns a zero row with
        status 200 (verified 2026-11-28). ``None`` means the API answered an
        empty list, which it did for unknown identifiers on 2026-11-27.
        """
        path = f"{INDEX_API_PATH}/citation-count/{normalize_index_id(id)}"
        return await _fetch_count(self._client, path)

    async def reference_count(self, id: str) -> int | None:
        """Return the number of outgoing references of one entity.

        An unknown identifier answers ``0``; see :meth:`citation_count`.
        """
        path = f"{INDEX_API_PATH}/reference-count/{normalize_index_id(id)}"
        return await _fetch_count(self._client, path)

    async def venue_citation_count(self, issn: str) -> int | None:
        """Return the number of incoming citations to a whole venue.

        ``issn`` is an ``issn:``-prefixed identifier; this is the only
        scheme the operation accepts. An unknown identifier answers ``0``;
        see :meth:`citation_count`.
        """
        path = f"{INDEX_API_PATH}/venue-citation-count/{normalize_issn(issn)}"
        return await _fetch_count(self._client, path)

    async def sparql(
        self,
        query: str,
        *,
        method: SparqlMethod = "GET",
        timeout: float | None = None,
    ) -> SparqlResult:
        """Run a SPARQL SELECT or ASK query on the Index dataset.

        The endpoint is ``https://sparql.opencitations.net/index``. A SELECT
        answer fills ``results``, and ``rows()`` on the result returns the
        bindings as plain strings. An ASK answer fills ``boolean``. The
        ``meta`` member carries the query time and the number of rows.

        ``method="POST"`` sends the query in the request body, which has no
        length limit. A malformed query answers 400 and raises
        :class:`~bibliofabric.exceptions.APIError` with the server's message
        in the body.
        """
        return await _run_sparql(
            self._client, INDEX_SPARQL_URL, query, method=method, timeout=timeout
        )

    async def sparql_text(
        self,
        query: str,
        *,
        format: str = "turtle",
        method: SparqlMethod = "GET",
        timeout: float | None = None,
    ) -> str:
        """Run a SPARQL query and return the raw body as text.

        ``format`` selects the representation through the ``Accept``
        header: ``json``, ``xml``, ``csv``, ``tsv``, ``turtle``, or
        ``n-triples``. CONSTRUCT and DESCRIBE answers are RDF, so use this
        method for them: the endpoint answers Turtle for a CONSTRUCT query
        that asks for the JSON representation (verified 2026-11-28).
        """
        return await _run_sparql_text(
            self._client,
            INDEX_SPARQL_URL,
            query,
            format=format,
            method=method,
            timeout=timeout,
        )


class MetaClient:
    """The read operations of the OpenCitations Meta API v1.

    The rows share the shape of :class:`~opcitato.models.MetadataRecord`;
    missing values are empty strings. The row-shaping parameters behave as
    in the Index API. The SPARQL endpoint of the Meta dataset answers
    arbitrary queries through :meth:`sparql` and :meth:`sparql_text`.
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def metadata(
        self,
        ids: str | Sequence[str],
        *,
        require: str | Sequence[str] | None = None,
        filter: str | Sequence[str] | None = None,
        sort: str | None = None,
        format: RowFormat = "json",
    ) -> list[MetadataRecord]:
        """Return the bibliographic metadata of one or more entities.

        ``ids`` is one prefixed identifier or a list of them; the accepted
        schemes are ``doi``, ``issn``, ``isbn``, ``omid``, ``openalex``,
        ``pmid``, and ``pmcid``. Several identifiers are packed into one
        request with the ``__`` separator, and one answer row comes back
        per identifier found. An unknown identifier contributes no row.
        """
        path = f"{META_API_PATH}/metadata/{normalize_meta_ids(ids)}"
        params = _row_params(require=require, filter=filter, sort=sort, format=format)
        return await _fetch_rows(self._client, MetadataRecord, path, params)

    async def author(
        self,
        id: str,
        *,
        require: str | Sequence[str] | None = None,
        filter: str | Sequence[str] | None = None,
        sort: str | None = None,
        format: RowFormat = "json",
    ) -> list[MetadataRecord]:
        """Return the entities the person with this identifier authored.

        ``id`` is ``orcid:0000-0002-8420-0696`` or the OpenCitations id of
        a responsible entity (``omid:ra/0601``).
        """
        path = f"{META_API_PATH}/author/{normalize_person_id(id)}"
        params = _row_params(require=require, filter=filter, sort=sort, format=format)
        return await _fetch_rows(self._client, MetadataRecord, path, params)

    async def editor(
        self,
        id: str,
        *,
        require: str | Sequence[str] | None = None,
        filter: str | Sequence[str] | None = None,
        sort: str | None = None,
        format: RowFormat = "json",
    ) -> list[MetadataRecord]:
        """Return the entities the person with this identifier edited.

        ``id`` is an ``orcid:`` or ``omid:ra/`` identifier, as in
        :meth:`author`.
        """
        path = f"{META_API_PATH}/editor/{normalize_person_id(id)}"
        params = _row_params(require=require, filter=filter, sort=sort, format=format)
        return await _fetch_rows(self._client, MetadataRecord, path, params)

    async def sparql(
        self,
        query: str,
        *,
        method: SparqlMethod = "GET",
        timeout: float | None = None,
    ) -> SparqlResult:
        """Run a SPARQL SELECT or ASK query on the Meta dataset.

        The endpoint is ``https://sparql.opencitations.net/meta``. The
        answer follows the same shape as in
        :meth:`IndexClient.sparql`.
        """
        return await _run_sparql(
            self._client, META_SPARQL_URL, query, method=method, timeout=timeout
        )

    async def sparql_text(
        self,
        query: str,
        *,
        format: str = "turtle",
        method: SparqlMethod = "GET",
        timeout: float | None = None,
    ) -> str:
        """Run a SPARQL query and return the raw body as text.

        The parameters behave exactly as in
        :meth:`IndexClient.sparql_text`.
        """
        return await _run_sparql_text(
            self._client,
            META_SPARQL_URL,
            query,
            format=format,
            method=method,
            timeout=timeout,
        )


__all__ = [
    "IndexClient",
    "MetaClient",
    "RowFormat",
    "SPARQL_MEDIA_TYPES",
    "SparqlMethod",
]
