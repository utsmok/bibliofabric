"""Resource clients for the ORCID Public API routes.

Paths are ``/{orcid}/{section}``, so every resource client overrides
:meth:`item_path` to put the ORCID iD first. Section routes answer 404 when
the record has none of that kind (verified for ``biography`` and ``emails``
on 2026-11-27), so the section readers turn a 404 into ``None`` by default.
"""

from collections.abc import Sequence
from typing import Any, override
from urllib.parse import quote

from bibliofabric import BaseApiClient, ResourceClient, validate_model
from bibliofabric.exceptions import ConfigurationError, NotFoundError
from bibliofabric.ids import normalize_orcid
from pydantic import BaseModel

from ..dialect import (
    ORCID_ITEM_DIALECT,
    ORCID_SEARCH_DIALECT,
    PERSON_ITEM_KINDS,
    WORKS_BULK_MAX,
)
from ..models import (
    ActivitiesSummary,
    Addresses,
    Biography,
    DistinctionsSection,
    EducationsSection,
    Emails,
    EmploymentsSection,
    ExpandedResult,
    ExternalIdentifiers,
    Funding,
    FundingsSection,
    InvitedPositionsSection,
    Keywords,
    MembershipsSection,
    OrchisRecord,
    OtherNames,
    PeerReview,
    PeerReviewsSection,
    Person,
    PersonalDetails,
    QualificationsSection,
    ResearcherUrls,
    ResearchResourcesSection,
    ServicesSection,
    SolrResult,
    Work,
    WorksSection,
)


async def _fetch_model[M: BaseModel](
    client: BaseApiClient,
    path: str,
    model: type[M],
    *,
    not_found_ok: bool = False,
) -> M | None:
    """Fetch one route and validate the body against ``model``."""
    try:
        response = await client.request("GET", path)
    except NotFoundError:
        if not_found_ok:
            return None
        raise
    body = client.parse_json(response)
    return validate_model(
        model, body, request=getattr(response, "request", None), response=response
    )


class OrchisResourceClient[E: BaseModel](ResourceClient[E]):
    """Base client for ORCID resources: ORCID iD normalization and paths."""

    dialect = ORCID_ITEM_DIALECT
    suffix = ""

    @override
    def normalize_id(self, value: str) -> str:
        """Return the hyphenated ORCID iD (URLs and compact forms accepted)."""
        return normalize_orcid(value)

    @override
    def item_path(self, id: str | int) -> str:
        """Return ``/{orcid}/{suffix}`` for the record-bound route."""
        orcid = self.normalize_id(str(id))
        if not orcid:
            raise ConfigurationError(
                f"{type(self).__name__}.item_path requires a non-empty ORCID iD."
            )
        return f"{quote(orcid, safe='')}/{self.suffix}"

    @override
    async def exists(self, id: str | int) -> bool:
        """Return ``True`` when the record exists; 404 returns ``False``.

        Uses ``GET`` so the check does not depend on ``HEAD`` support.
        """
        try:
            await self.get(id)
        except NotFoundError:
            return False
        return True

    def _base(self, orcid: str) -> str:
        """Return the URL-encoded, normalized ORCID iD path segment."""
        return quote(self.normalize_id(orcid), safe="")


class RecordClient(OrchisResourceClient[OrchisRecord]):
    """Client for the record summary route (``/{orcid}/record``)."""

    model = OrchisRecord
    suffix = "record"

    async def representation(self, orcid: str, accept: str = "application/xml") -> str:
        """Return the record in another representation as text.

        ``application/xml`` is served today; ``application/ld+json`` answers
        406 on the public API (verified 2026-11-27).
        """
        response = await self._client.request(
            "GET", self.item_path(orcid), headers={"Accept": accept}
        )
        return response.text


class PersonClient(OrchisResourceClient[Person]):
    """Client for the person section and its sub-section routes."""

    model = Person
    suffix = "person"

    async def personal_details(self, orcid: str) -> PersonalDetails | None:
        """Fetch ``/{orcid}/personal-details``; ``None`` on a missing record."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/personal-details",
            PersonalDetails,
            not_found_ok=True,
        )

    async def biography(self, orcid: str) -> Biography | None:
        """Fetch ``/{orcid}/biography``; ``None`` when the record has none."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/biography",
            Biography,
            not_found_ok=True,
        )

    async def researcher_urls(self, orcid: str) -> ResearcherUrls | None:
        """Fetch ``/{orcid}/researcher-urls``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/researcher-urls",
            ResearcherUrls,
            not_found_ok=True,
        )

    async def emails(self, orcid: str) -> Emails | None:
        """Fetch ``/{orcid}/emails``; ``None`` when the record has none."""
        return await _fetch_model(
            self._client, f"{self._base(orcid)}/emails", Emails, not_found_ok=True
        )

    async def addresses(self, orcid: str) -> Addresses | None:
        """Fetch ``/{orcid}/address``."""
        return await _fetch_model(
            self._client, f"{self._base(orcid)}/address", Addresses, not_found_ok=True
        )

    async def keywords(self, orcid: str) -> Keywords | None:
        """Fetch ``/{orcid}/keywords``."""
        return await _fetch_model(
            self._client, f"{self._base(orcid)}/keywords", Keywords, not_found_ok=True
        )

    async def external_identifiers(self, orcid: str) -> ExternalIdentifiers | None:
        """Fetch ``/{orcid}/external-identifiers``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/external-identifiers",
            ExternalIdentifiers,
            not_found_ok=True,
        )

    async def other_names(self, orcid: str) -> OtherNames | None:
        """Fetch ``/{orcid}/other-names``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/other-names",
            OtherNames,
            not_found_ok=True,
        )

    async def item(self, orcid: str, kind: str, put_code: int) -> dict[str, Any]:
        """Fetch one person item as the parsed JSON object.

        ``kind`` is the route segment of the section: ``address``,
        ``keywords``, ``other-names``, ``researcher-urls``, or
        ``external-identifiers``. The section routes above return the same
        items in their lists.
        """
        if kind not in PERSON_ITEM_KINDS:
            raise ConfigurationError(
                f"kind must be one of {sorted(PERSON_ITEM_KINDS)}, got {kind!r}."
            )
        response = await self._client.request(
            "GET", f"{self._base(orcid)}/{kind}/{put_code}"
        )
        body = self._client.parse_json(response)
        if not isinstance(body, dict):
            raise ConfigurationError(f"ORCID answered a non-object body for {kind}.")
        return body


class ActivitiesClient(OrchisResourceClient[ActivitiesSummary]):
    """Client for the activities summary, its sections, and single items.

    Section readers return ``None`` when the record has none of that kind;
    the API answers 404 for such sections (verified 2026-11-27 for a record
    without distinctions, qualifications, and similar empty sections).
    """

    model = ActivitiesSummary
    suffix = "activities"

    async def works(self, orcid: str) -> WorksSection | None:
        """Fetch ``/{orcid}/works``."""
        return await _fetch_model(
            self._client, f"{self._base(orcid)}/works", WorksSection, not_found_ok=True
        )

    async def educations(self, orcid: str) -> EducationsSection | None:
        """Fetch ``/{orcid}/educations``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/educations",
            EducationsSection,
            not_found_ok=True,
        )

    async def employments(self, orcid: str) -> EmploymentsSection | None:
        """Fetch ``/{orcid}/employments``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/employments",
            EmploymentsSection,
            not_found_ok=True,
        )

    async def fundings(self, orcid: str) -> FundingsSection | None:
        """Fetch ``/{orcid}/fundings``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/fundings",
            FundingsSection,
            not_found_ok=True,
        )

    async def peer_reviews(self, orcid: str) -> PeerReviewsSection | None:
        """Fetch ``/{orcid}/peer-reviews``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/peer-reviews",
            PeerReviewsSection,
            not_found_ok=True,
        )

    async def distinctions(self, orcid: str) -> DistinctionsSection | None:
        """Fetch ``/{orcid}/distinctions``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/distinctions",
            DistinctionsSection,
            not_found_ok=True,
        )

    async def invited_positions(self, orcid: str) -> InvitedPositionsSection | None:
        """Fetch ``/{orcid}/invited-positions``.

        The invitation-to-peer-review listing lives on
        ``/{orcid}/peer-reviews``; the activities summary names this section
        ``invited-positions``.
        """
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/invited-positions",
            InvitedPositionsSection,
            not_found_ok=True,
        )

    async def memberships(self, orcid: str) -> MembershipsSection | None:
        """Fetch ``/{orcid}/memberships``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/memberships",
            MembershipsSection,
            not_found_ok=True,
        )

    async def qualifications(self, orcid: str) -> QualificationsSection | None:
        """Fetch ``/{orcid}/qualifications``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/qualifications",
            QualificationsSection,
            not_found_ok=True,
        )

    async def research_resources(self, orcid: str) -> ResearchResourcesSection | None:
        """Fetch ``/{orcid}/research-resources``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/research-resources",
            ResearchResourcesSection,
            not_found_ok=True,
        )

    async def services(self, orcid: str) -> ServicesSection | None:
        """Fetch ``/{orcid}/services``."""
        return await _fetch_model(
            self._client,
            f"{self._base(orcid)}/services",
            ServicesSection,
            not_found_ok=True,
        )

    async def work(self, orcid: str, put_code: int) -> Work:
        """Fetch one full work (``/{orcid}/work/{put-code}``)."""
        work = await _fetch_model(
            self._client, f"{self._base(orcid)}/work/{put_code}", Work
        )
        assert work is not None
        return work

    async def works_bulk(self, orcid: str, put_codes: Sequence[int]) -> list[Work]:
        """Fetch full works by put code, up to 100 per request.

        Uses ``/{orcid}/works/{code},{code},...`` and splits longer lists
        into requests of 100. ORCID answers an ``error`` entry for a put
        code it does not know; those codes are absent from the result.
        """
        codes = list(dict.fromkeys(int(code) for code in put_codes))
        works: list[Work] = []
        for start in range(0, len(codes), WORKS_BULK_MAX):
            chunk = ",".join(
                str(code) for code in codes[start : start + WORKS_BULK_MAX]
            )
            response = await self._client.request(
                "GET", f"{self._base(orcid)}/works/{chunk}"
            )
            body = self._client.parse_json(response)
            entries = body.get("bulk") if isinstance(body, dict) else None
            if not isinstance(entries, list):
                raise ConfigurationError("ORCID answered a works bulk without 'bulk'.")
            works.extend(
                validate_model(
                    Work, entry["work"], request=response.request, response=response
                )
                for entry in entries
                if isinstance(entry, dict) and isinstance(entry.get("work"), dict)
            )
        return works

    async def funding(self, orcid: str, put_code: int) -> Funding:
        """Fetch one full funding entry (``/{orcid}/funding/{put-code}``)."""
        funding = await _fetch_model(
            self._client, f"{self._base(orcid)}/funding/{put_code}", Funding
        )
        assert funding is not None
        return funding

    async def peer_review(self, orcid: str, put_code: int) -> PeerReview:
        """Fetch one full peer review (``/{orcid}/peer-review/{put-code}``)."""
        review = await _fetch_model(
            self._client, f"{self._base(orcid)}/peer-review/{put_code}", PeerReview
        )
        assert review is not None
        return review

    async def affiliation_item(
        self, orcid: str, kind: str, put_code: int
    ) -> dict[str, Any]:
        """Fetch one qualification, membership, service, or similar item.

        ``kind`` is the singular route segment (``qualification``,
        ``membership``, ``service``, ``distinction``, ``invited-position``,
        or ``research-resource``). These single-item routes share the
        affiliation shape, so the client returns the parsed JSON object
        instead of one model per kind.
        """
        known = {
            "qualification",
            "membership",
            "service",
            "distinction",
            "invited-position",
            "research-resource",
        }
        if kind not in known:
            raise ConfigurationError(
                f"kind must be one of {sorted(known)}, got {kind!r}."
            )
        return await self._fetch_raw(f"{self._base(orcid)}/{kind}/{put_code}")

    async def education(self, orcid: str, put_code: int) -> dict[str, Any]:
        """Fetch one education item (``/{orcid}/education/{put-code}``)."""
        return await self._fetch_raw(f"{self._base(orcid)}/education/{put_code}")

    async def employment(self, orcid: str, put_code: int) -> dict[str, Any]:
        """Fetch one employment item (``/{orcid}/employment/{put-code}``)."""
        return await self._fetch_raw(f"{self._base(orcid)}/employment/{put_code}")

    async def representation(
        self, orcid: str, suffix: str, accept: str = "application/xml"
    ) -> str:
        """Return any route under the ORCID iD in another representation.

        For example ``representation(orcid, "work/1234")`` returns the work
        as XML text.
        """
        response = await self._client.request(
            "GET",
            f"{self._base(orcid)}/{suffix.lstrip('/')}",
            headers={"Accept": accept},
        )
        return response.text

    async def _fetch_raw(self, path: str) -> dict[str, Any]:
        """Fetch one route and return the parsed JSON object."""
        response = await self._client.request("GET", path)
        body = self._client.parse_json(response)
        if not isinstance(body, dict):
            raise ConfigurationError(f"ORCID answered a non-object body for {path}.")
        return body


class ExpandedSearchClient(OrchisResourceClient[ExpandedResult]):
    """Client for the expanded search route (``/expanded-search``).

    The route answers an expanded profile per result (names, emails,
    institutions). ``rows`` sets the page size and ``start`` the zero-based
    offset, both through the dialect paging.
    """

    path = "expanded-search/"
    dialect = ORCID_SEARCH_DIALECT
    model = ExpandedResult

    @override
    async def search(self, filters=None, *, query=None, **kwargs):
        """Fetch one page of expanded search results (``query`` required)."""
        if query is None:
            raise ConfigurationError("expanded search requires a query string.")
        return await super().search(filters, query=query, **kwargs)

    async def csv(
        self,
        query: str,
        *,
        fields: Sequence[str] | None = None,
        rows: int | None = None,
        start: int | None = None,
    ) -> str:
        """Return one page of the CSV search (``/csv-search``) as text.

        The route searches the same index as the expanded search and answers
        CSV with a header row. ``fields`` picks the columns (the ``fl``
        parameter, for example ``["orcid", "given-names", "family-name"]``);
        without it ORCID answers its nine default columns.
        """
        if not query:
            raise ConfigurationError("csv search requires a query string.")
        params: dict[str, Any] = {"q": query}
        if fields:
            params["fl"] = ",".join(fields)
        if rows is not None:
            params["rows"] = rows
        if start is not None:
            params["start"] = start
        response = await self._client.request(
            "GET", "csv-search/", params=params, headers={"Accept": "text/csv"}
        )
        return response.text


class SolrSearchClient(OrchisResourceClient[SolrResult]):
    """Client for the Solr-compatible search route (``/search``).

    The route answers the same Solr index with one ``orcid-identifier`` per
    result and accepts the same ``rows`` and ``start`` paging.
    """

    path = "search/"
    dialect = ORCID_SEARCH_DIALECT
    model = SolrResult

    @override
    async def search(self, filters=None, *, query=None, **kwargs):
        """Fetch one page of Solr search results (``query`` required)."""
        if query is None:
            raise ConfigurationError("search requires a query string.")
        return await super().search(filters, query=query, **kwargs)


__all__ = [
    "ActivitiesClient",
    "ExpandedSearchClient",
    "PersonClient",
    "RecordClient",
    "SolrSearchClient",
    "OrchisResourceClient",
]
