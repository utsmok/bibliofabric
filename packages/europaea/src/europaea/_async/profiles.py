"""Client for the Europe PMC profile endpoint."""

from bibliofabric import BaseApiClient, validate_model

from ..models import FieldsResponse, ProfileResponse


class ProfilesClient:
    """Client for the ``/profile`` and ``/fields`` endpoints.

    The profile route reports how many articles match one author or grant
    query per source and publication type; it is a single request, not paged.
    """

    def __init__(self, client: BaseApiClient) -> None:
        """Build the profiles client over an owning :class:`EuropaeaClient`."""
        self._client = client

    async def profile(
        self, query: str, *, profile_type: str = "all", synonym: bool = False
    ) -> ProfileResponse:
        """Return the article counts of one profile query.

        Args:
            query: Europe PMC query string, usually an author query such as
                ``"AUTH:%22Mok S%22"`` or a grant query.
            profile_type: ``"all"``, ``"lite"``, or ``"core"``.
            synonym: Expand query terms with MeSH synonyms.
        """
        body = await self._client.get_json(
            "profile",
            params={
                "query": query,
                "profiletype": profile_type,
                "synonym": "true" if synonym else "false",
                "format": "json",
            },
        )
        return validate_model(ProfileResponse, body)

    async def fields(self) -> FieldsResponse:
        """Return the searchable index terms of the REST search."""
        body = await self._client.get_json("fields", params={"format": "json"})
        return validate_model(FieldsResponse, body)


__all__ = ["ProfilesClient"]
