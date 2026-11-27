"""The shared resource-client base for the OpenAlex entity endpoints.

:class:`OpenAlexResourceClient` encodes the OpenAlex API shape on top of
bibliofabric's generic :class:`bibliofabric.ResourceClient`: the single
``filter=`` parameter, pipe-joined OR batches of up to 100 ids, DOI/ORCID/ROR
normalization, cursor iteration at ``per_page=100``, and a minimal-cost
``count()``. The query-dialect constants it consumes live in the pure module
:mod:`aletheca.dialect`.
"""

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import quote

from bibliofabric import ResourceClient
from bibliofabric.exceptions import ConfigurationError
from bibliofabric.ids import (
    is_doi,
    normalize_doi,
    normalize_issn,
    normalize_orcid,
    normalize_ror,
    strip_url_prefix,
)
from pydantic import BaseModel

from ..dialect import (
    _OPENALEX_URL_PREFIX,
    MAX_BASIC_PAGING_RESULTS,
    MAX_OR_VALUES,
    OPENALEX_DIALECT,
)

#: Filter fields whose values are DOIs and need prefix/case normalization
#: before they may join a ``filter=`` value (raw URL forms inject colons).
DOI_FIELDS = frozenset({"doi", "funder.doi"})

_ORCID_PATTERN = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dXx]$")
_ROR_PATTERN = re.compile(r"^0[a-hj-km-np-tv-z0-9]{6}\d{2}$")
_ISSN_PATTERN = re.compile(r"^\d{4}-\d{3}[\dXx]$")
_PMCID_PATTERN = re.compile(r"^PMC\d+$", re.IGNORECASE)

_ORCID_PREFIXES = ("https://orcid.org/", "http://orcid.org/", "orcid:")
_ROR_PREFIXES = ("https://ror.org/", "http://ror.org/", "ror:")
_PMID_PREFIXES = (
    "https://pubmed.ncbi.nlm.nih.gov/",
    "http://pubmed.ncbi.nlm.nih.gov/",
    "pmid:",
)
_PMCID_PREFIXES = (
    "https://www.ncbi.nlm.nih.gov/pmc/articles/",
    "http://www.ncbi.nlm.nih.gov/pmc/articles/",
    "https://pmc.ncbi.nlm.nih.gov/articles/",
    "http://pmc.ncbi.nlm.nih.gov/articles/",
    "pmcid:",
)
_ISSN_PREFIXES = ("issn:",)


def _normalize_filter_value(field: str, value: Any) -> str:
    """Stringify one filter value the way OpenAlex expects.

    Booleans serialize lowercase (``is_oa:true``); lists/tuples/sets join with
    ``|`` (OR), DOIs inside OR lists are normalized first. Values that carry
    spaces or commas need quoting by the caller (OpenAlex rule).
    """
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list | tuple | set | frozenset):
        items = sorted(value, key=str) if isinstance(value, set | frozenset) else value
        values = [str(item) for item in items]
        if field in DOI_FIELDS:
            values = [normalize_doi(item) for item in values]
        if len(values) > MAX_OR_VALUES:
            raise ConfigurationError(
                f"OpenAlex allows at most {MAX_OR_VALUES} pipe-separated "
                f"values per filter; got {len(values)} for '{field}'."
            )
        return "|".join(values)
    if field in DOI_FIELDS:
        return normalize_doi(str(value))
    return str(value)


def serialize_filter_params(
    filters: BaseModel | Mapping[str, Any] | None,
) -> dict[str, str]:
    """Serialize filter criteria into OpenAlex's single ``filter`` parameter.

    ``filter=publication_year:2024,is_oa:true``; list/tuple/set values become
    pipe-joined OR groups (max :data:`MAX_OR_VALUES`). ``None`` entries and
    empty collections are omitted.
    """
    if filters is None:
        return {}
    if isinstance(filters, BaseModel):
        dumped = filters.model_dump(exclude_none=True, by_alias=True)
    else:
        dumped = {key: value for key, value in filters.items() if value is not None}
    parts: list[str] = []
    for key, value in dumped.items():
        if isinstance(value, list | tuple | set | frozenset) and not value:
            continue
        parts.append(f"{key}:{_normalize_filter_value(key, value)}")
    if not parts:
        return {}
    return {"filter": ",".join(parts)}


class OpenAlexResourceClient[E: BaseModel](ResourceClient[E]):
    """Base for all OpenAlex resource clients."""

    dialect = OPENALEX_DIALECT
    batch_size = MAX_OR_VALUES

    # --- hooks ---------------------------------------------------------

    def normalize_id(self, value: str) -> str:
        """Canonicalize an identifier used in paths, batches, and dict keys.

        Strips ``https://openalex.org/`` and the entity path prefix, and
        normalizes DOIs, ORCIDs, RORs, ISSNs, PMIDs, and PMCIDs so caller
        inputs and returned record keys match across ``batch_get`` and
        filters.
        """
        text = value.strip()
        text = text.removeprefix(_OPENALEX_URL_PREFIX)
        text = text.removeprefix(f"{self.path}/")
        if is_doi(text):
            return normalize_doi(text)
        lower = text.lower()
        if lower.startswith(_ORCID_PREFIXES) or _ORCID_PATTERN.match(text):
            return normalize_orcid(text)
        if lower.startswith(_ROR_PREFIXES):
            return normalize_ror(text)
        if lower.startswith(_PMID_PREFIXES):
            return strip_url_prefix(text, _PMID_PREFIXES).rstrip("/")
        if lower.startswith(_PMCID_PREFIXES):
            return strip_url_prefix(text, _PMCID_PREFIXES).rstrip("/").upper()
        if lower.startswith(_ISSN_PREFIXES) or _ISSN_PATTERN.match(text):
            return normalize_issn(strip_url_prefix(text, _ISSN_PREFIXES))
        return text

    def item_path(self, id: str | int) -> str:
        """Return the single-entity path for ``id`` with external-ID prefixes.

        OpenAlex bills bare DOI paths (``/works/10.7717/...``) at $0.0001
        whereas prefixed singletons (``/works/doi%3A10.7717%2F...``) are free
        ($0). External IDs (DOI, ORCID, ROR, ISSN, PMID, PMCID) therefore get
        their namespace prefix before URL-encoding.
        """
        normalized = self.normalize_id(str(id))
        if not normalized:
            raise ConfigurationError(
                f"{type(self).__name__}.item_path requires a non-empty id."
            )
        lower = normalized.lower()
        if is_doi(normalized) and not lower.startswith("doi:"):
            path_id = f"doi:{normalized}"
        elif _ORCID_PATTERN.match(normalized):
            path_id = f"orcid:{normalized}"
        elif _ROR_PATTERN.match(normalized) and self.path in (
            "institutions",
            "funders",
            "publishers",
        ):
            path_id = f"ror:{normalized}"
        elif _ISSN_PATTERN.match(normalized) and self.path == "sources":
            path_id = f"issn:{normalized}"
        elif normalized.isdigit() and self.path == "works":
            path_id = f"pmid:{normalized}"
        elif _PMCID_PATTERN.match(normalized) and self.path == "works":
            path_id = f"pmcid:{normalized.upper()}"
        else:
            path_id = normalized
        return f"{self.path.rstrip('/')}/{quote(path_id, safe='')}"

    def record_keys(self, entity: E, field: str) -> list[str]:
        """Return every normalized ``field`` value of ``entity``.

        Resolves OpenAlex's ``ids`` sub-object for external identifiers such as
        ``pmid``/``pmcid`` on works, ``orcid``/``observed_orcids`` on authors,
        ``ror`` on institutions, and ``issn``/``issn_l`` on sources, and maps
        ``field="openalex"`` to ``entity.id``.
        """
        attr = field.removeprefix("ids.")
        raw_values: list[Any] = []
        ids_obj = getattr(entity, "ids", None)
        if attr in ("id", "openalex"):
            top = getattr(entity, "id", None)
            if top is not None:
                raw_values.append(top)
            if ids_obj is not None:
                nested = getattr(ids_obj, "openalex", None)
                if nested is not None:
                    raw_values.append(nested)
        else:
            top = getattr(entity, attr, None)
            if top is not None:
                raw_values.extend(top if isinstance(top, list) else [top])
            if ids_obj is not None:
                nested = getattr(ids_obj, attr, None)
                if nested is not None:
                    raw_values.extend(nested if isinstance(nested, list) else [nested])
            if attr == "orcid":
                observed = getattr(entity, "observed_orcids", None)
                if isinstance(observed, list):
                    raw_values.extend(observed)
                if ids_obj is not None:
                    nested_obs = getattr(ids_obj, "observed_orcids", None)
                    if isinstance(nested_obs, list):
                        raw_values.extend(nested_obs)
        if not raw_values:
            fallback = getattr(entity, "id", None)
            if fallback is not None:
                raw_values.append(fallback)
        return list(
            dict.fromkeys(
                self.normalize_id(str(item)) for item in raw_values if item is not None
            )
        )

    def build_filter_params(
        self, filters: BaseModel | Mapping[str, Any] | None
    ) -> dict[str, str]:
        """Serialize filters into OpenAlex's single ``filter`` parameter."""
        return serialize_filter_params(filters)

    def build_batch_params(self, field: str, values: Sequence[str]) -> dict[str, str]:
        """Build one ``batch_get`` chunk as a pipe-joined OR filter.

        DOI fields are normalized first (AT-03): URL forms would inject
        colons into the ``filter=`` value. The default ``field="id"`` maps to
        the ``openalex`` filter, because OpenAlex has no ``id`` filter.
        """
        chunk = list(values)
        if field in DOI_FIELDS:
            chunk = [normalize_doi(value) for value in chunk]
        filter_key = "openalex" if field == "id" else field
        return {"filter": f"{filter_key}:{'|'.join(chunk)}"}

    # --- internals -----------------------------------------------------

    def _search_params(
        self,
        *,
        filters: BaseModel | Mapping[str, Any] | None,
        query: str | None = None,
        sort: str | Sequence[str] | None = None,
        select: Sequence[str] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        cursor: str | None = None,
        params: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        if page is not None and cursor is not None:
            raise ConfigurationError(
                "Cannot combine 'page' and 'cursor' pagination parameters."
            )
        if page is not None and page < self.dialect.page_start:
            raise ConfigurationError(
                f"page must be >= {self.dialect.page_start}, got {page}."
            )
        if page_size is not None and page_size <= 0:
            raise ConfigurationError(f"page_size must be positive, got {page_size}.")
        if cursor is None and page is not None:
            size = (
                self.dialect.default_page_size
                if page_size is None
                else min(page_size, self.dialect.max_page_size)
            )
            if page * size > MAX_BASIC_PAGING_RESULTS:
                raise ConfigurationError(
                    f"OpenAlex caps basic paging at page * per_page <= "
                    f"{MAX_BASIC_PAGING_RESULTS} (requested page={page}, "
                    f"per_page={size}); use iterate() for deep result sets."
                )
        return super()._search_params(
            filters=filters,
            query=query,
            sort=sort,
            select=select,
            page=page,
            page_size=page_size,
            cursor=cursor,
            params=params,
        )

    # --- operations ----------------------------------------------------

    async def count(
        self,
        filters: BaseModel | Mapping[str, Any] | None = None,
        *,
        query: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> int:
        """Return the total number of matching entities at minimal cost.

        Sends ``per_page=1`` (the core default) plus ``select=id`` so the
        one-credit count request carries no entity payloads.
        """
        merged = {"select": "id", **(params or {})}
        return await super().count(filters, query=query, params=merged)
