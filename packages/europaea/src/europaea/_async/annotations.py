"""Client for the Europe PMC annotations API."""

from collections.abc import Mapping
from typing import Any

from bibliofabric import BaseApiClient, validate_model
from bibliofabric.exceptions import ConfigurationError

from ..models import AnnotationPage, ArticleAnnotations
from .resources import ANNOTATIONS_API_BASE_URL

AnnotationType = str
"""Annotation type values include ``ACC``, ``ACCESSION``, ``CHEBI``, ``CLO``,
``Cheatr``, ``Diseases``, ``EFO``, ``GO_Biological_Process``, ``GO_Cellular_Component``,
``GO_Molecular_Function``, ``MOL``, ``Panther``, ``REACT``, ``Taxonomy``, and
``UNIPROT``; the exact set grows with the annotation providers."""

_JSON_FORMAT = "JSON"


class AnnotationsClient:
    """Client for the ``annotations_api`` endpoints.

    The annotations API is a separate service from the REST web services
    (base URL ``https://www.ebi.ac.uk/europepmc/annotations_api``). It has
    five query routes; all answer JSON.
    """

    def __init__(self, client: BaseApiClient) -> None:
        """Build the annotations client over an owning :class:`EuropaeaClient`.

        Args:
            client: The owning client; requests reuse its HTTP pool, rate
                limiter, and retry policy.
        """
        self._client = client

    async def by_article_ids(
        self,
        article_ids: str | list[str],
        *,
        type: str | None = None,
        sub_type: str | None = None,
        section: str | None = None,
        provider: str | None = None,
    ) -> list[ArticleAnnotations]:
        """Return the annotations of one or more articles.

        Args:
            article_ids: One article id (``"MED:23903748"``) or a list of
                them, comma-joined into the ``articleIds`` parameter.
            type: Annotation type filter (for example ``"Chemicals"``).
            section: Article section filter (for example ``"Methods"``).

        Returns:
            One record per article, each carrying its annotation list.
        """
        ids = ",".join(article_ids) if isinstance(article_ids, list) else article_ids
        params: dict[str, str] = {"articleIds": ids, "format": _JSON_FORMAT}
        if type:
            params["type"] = type
        if sub_type:
            params["subType"] = sub_type
        if section:
            params["section"] = section
        if provider:
            params["provider"] = provider
        body = await self._get("/annotationsByArticleIds", params)
        records = body if isinstance(body, list) else []
        return [validate_model(ArticleAnnotations, record) for record in records]

    async def by_entity(
        self,
        entity: str,
        *,
        filter: str | None = None,
        cursor: float | str | None = None,
        page_size: int | None = None,
    ) -> AnnotationPage:
        """Return the articles annotated with ``entity`` (cursor paged).

        ``cursor`` takes ``next_cursor_mark`` of the previous page; ``None``
        starts at the first page. The API reports exhaustion by repeating a
        cursor of ``-1.0``, which maps to ``next_cursor_mark=None``.
        """
        return await self._paged(
            "/annotationsByEntity",
            {"entity": entity, "filter": filter},
            cursor,
            page_size,
        )

    async def by_provider(
        self,
        provider: str,
        *,
        filter: str | None = None,
        cursor: float | str | None = None,
        page_size: int | None = None,
    ) -> AnnotationPage:
        """Return the annotations of one provider (cursor paged).

        ``provider`` is a provider name such as ``"Europe PMC"``,
        ``"OpenTargets"``, or ``"HES-SO_SIB"``; invalid names answer 400.
        """
        return await self._paged(
            "/annotationsByProvider",
            {"provider": provider, "filter": filter},
            cursor,
            page_size,
        )

    async def by_relationship(
        self,
        first_entity: str,
        second_entity: str,
        *,
        filter: str | None = None,
        cursor: float | str | None = None,
        page_size: int | None = None,
    ) -> AnnotationPage:
        """Return articles whose annotations relate two entities (cursor paged)."""
        return await self._paged(
            "/annotationsByRelationship",
            {
                "firstEntity": first_entity,
                "secondEntity": second_entity,
                "filter": filter,
            },
            cursor,
            page_size,
        )

    async def by_section(
        self,
        *,
        type: str | None = None,
        sub_type: str | None = None,
        section: str | None = None,
        filter: str | None = None,
        cursor: float | str | None = None,
        page_size: int | None = None,
    ) -> AnnotationPage:
        """Return annotations filtered by type, subtype, and article section.

        This route is large: without filters it covers the whole annotation
        store. Always pass at least ``section`` or ``type``.
        """
        if type is None and section is None:
            raise ConfigurationError(
                "annotations by section needs a type, sub_type, or section filter."
            )
        return await self._paged(
            "/annotationsBySectionAndOrType",
            {"type": type, "subType": sub_type, "section": section, "filter": filter},
            cursor,
            page_size,
        )

    async def _get(self, path: str, params: Mapping[str, Any]) -> Any:
        """Send one GET against the annotations API base URL."""
        return await self._client.get_json(
            f"{ANNOTATIONS_API_BASE_URL}{path}",
            params={key: value for key, value in params.items() if value is not None},
        )

    async def _paged(
        self,
        path: str,
        selectors: Mapping[str, str | None],
        cursor: float | str | None,
        page_size: int | None,
    ) -> AnnotationPage:
        """Send one paged annotations query and map the envelope to a model."""
        params: dict[str, Any] = {**selectors, "format": _JSON_FORMAT}
        if cursor is not None:
            params["cursorMark"] = str(cursor)
        if page_size is not None:
            params["pageSize"] = page_size
        body = await self._get(path, params)
        page = validate_model(AnnotationPage, body)
        if page.next_cursor_mark is not None and page.next_cursor_mark < 0:
            page.next_cursor_mark = None
        return page


__all__ = ["AnnotationsClient", "AnnotationType"]
