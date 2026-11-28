"""Resource clients for the OpenCitations Index API v2 and Meta API v1.

Both APIs are unpaged: every operation answers with the complete result of
the query. Every operation accepts the row-shaping parameters ``require``,
``filter``, ``sort``, and ``format`` that the RAMOSE engine applies in that
order; ``format="csv"`` parses into the same models as the JSON form
because the CSV header repeats the JSON field names.
"""

from collections.abc import Sequence
from typing import Any, Literal
from urllib.parse import urlencode

from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError
from pydantic import BaseModel

from ..csvparse import parse_csv_rows
from ..dialect import FORMATS, INDEX_API_PATH, META_API_PATH
from ..ids import (
    normalize_index_id,
    normalize_issn,
    normalize_meta_ids,
    normalize_oci,
    normalize_person_id,
)
from ..models import Citation, Count, MetadataRecord

#: Result representation of an operation; ``format=csv`` overrides the
#: ``Accept`` header server-side.
RowFormat = Literal["json", "csv"]

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
    request = getattr(response, "request", None)
    return [
        validate_model(model, row, request=request, response=response) for row in rows
    ]


async def _fetch_count(client: BaseApiClient, path: str) -> int | None:
    """Send one count request and return the count, or ``None`` for ``[]``.

    An unknown identifier is not an error: the API answers 200 with an
    empty list, and this reads it as "no count reported".
    """
    response = await client.request("GET", path)
    body = client.parse_json(response)
    if not isinstance(body, list) or not body:
        return None
    request = getattr(response, "request", None)
    return validate_model(Count, body[0], request=request, response=response).count


class IndexClient:
    """The read operations of the OpenCitations Index API v2.

    Every operation sends one GET and returns the complete result; the API
    has no paging. ``citations`` and ``references`` accept ``require``,
    ``filter``, ``sort``, and ``format``; ``filter`` entries look like
    ``creation:>2019-12`` (a regular expression, or ``=``, ``<``, ``>``
    with a value), and ``sort`` looks like ``desc(creation)``.
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

        Returns ``None`` when the entity is unknown (the API answers ``[]``
        with status 200 instead of an error or a zero row).
        """
        path = f"{INDEX_API_PATH}/citation-count/{normalize_index_id(id)}"
        return await _fetch_count(self._client, path)

    async def reference_count(self, id: str) -> int | None:
        """Return the number of outgoing references of one entity.

        Returns ``None`` when the entity is unknown.
        """
        path = f"{INDEX_API_PATH}/reference-count/{normalize_index_id(id)}"
        return await _fetch_count(self._client, path)

    async def venue_citation_count(self, issn: str) -> int | None:
        """Return the number of incoming citations to a whole venue.

        ``issn`` is an ``issn:``-prefixed identifier; this is the only
        scheme the operation accepts.
        """
        path = f"{INDEX_API_PATH}/venue-citation-count/{normalize_issn(issn)}"
        return await _fetch_count(self._client, path)


class MetaClient:
    """The read operations of the OpenCitations Meta API v1.

    The rows share the shape of :class:`MetadataRecord`; missing values are
    empty strings. The row-shaping parameters behave as in the Index API.
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


__all__ = ["IndexClient", "MetaClient", "RowFormat"]
