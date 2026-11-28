"""Client for the public DataCite GraphQL API."""

import logging
from collections.abc import Mapping
from typing import Any

from bibliofabric import BaseApiClient
from bibliofabric.exceptions import APIError, ConfigurationError

logger = logging.getLogger(__name__)

GRAPHQL_PATH = "graphql"


class GraphqlClient:
    """The public GraphQL API of DataCite.

    The schema covers the same records as the REST API (works, persons,
    organizations, repositories, funders, prefixes, and events) and adds the
    connections between them. Queries need no credentials. Mutations need
    a bearer token and are out of scope.
    """

    def __init__(self, client: BaseApiClient) -> None:
        self._client = client

    async def query(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run one GraphQL query and return its ``data`` object.

        Args:
            query: The GraphQL document, for example
                ``{ work(id: "https://doi.org/10.5438/0012") { doi } }``.
            variables: Values for the variables that ``query`` declares.

        Returns:
            The ``data`` object of the answer, as plain dictionaries and
            lists. The answer shape follows the query, so the client does
            not validate it.

        Raises:
            ConfigurationError: ``query`` is empty.
            APIError: DataCite rejected the query, or a field failed. The
                ``body`` of the error holds the ``errors`` list that
                DataCite sent.
        """
        if not query.strip():
            raise ConfigurationError("query must be a non-empty GraphQL document.")
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = dict(variables)
        response = await self._client.request(
            "POST", GRAPHQL_PATH, json=payload, retry=True
        )
        body = self._client.parse_json(response)
        request = getattr(response, "request", None)
        if not isinstance(body, dict):
            raise APIError(
                "DataCite GraphQL answered without a JSON object.",
                body=body,
                request=request,
                response=response,
            )
        errors = body.get("errors")
        if errors:
            raise APIError(
                _summarize_errors(errors),
                body=body,
                request=request,
                response=response,
            )
        data = body.get("data")
        if not isinstance(data, dict):
            raise APIError(
                "DataCite GraphQL answered without a data object.",
                body=body,
                request=request,
                response=response,
            )
        logger.debug("DataCite GraphQL query returned %d top-level fields.", len(data))
        return data


def _summarize_errors(errors: Any) -> str:
    """Return one message that lists every GraphQL error."""
    if isinstance(errors, list):
        messages = [
            str(error.get("message", error)) for error in errors if error is not None
        ]
    else:
        messages = [str(errors)]
    joined = "; ".join(message for message in messages if message)
    if joined:
        return f"DataCite GraphQL reported {len(messages)} error(s): {joined}"
    return "DataCite GraphQL reported an error without a message."


__all__ = ["GraphqlClient"]
