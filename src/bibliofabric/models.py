# bibliofabric/models.py
"""Core protocols and interfaces for the bibliofabric framework.

This module defines the essential protocols that enable the generic framework
to work with different API response structures through pluggable patterns.
The ResponseUnwrapper protocol is the key abstraction that allows any API
client implementation to define how their specific JSON response format
should be parsed and processed.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ResponseUnwrapper(Protocol):
    """Protocol for unwrapping API-specific response structures.

    This protocol defines the interface that concrete implementations must
    satisfy to enable the generic bibliofabric framework to work with any
    API's response format. Each method handles a specific aspect of response
    parsing that varies between different APIs.

    The protocol enables a clean separation between generic HTTP client logic
    and API-specific response handling, making it easy to support new APIs
    by implementing this interface without modifying the core framework.

    Example:
        For an OpenAIRE API response like:
        ```json
        {
            "header": {
                "total": 1000,  # [total]
                "nextCursor": "abc123"  # [nextCursor]
            },
            "results": [
                {"id": "1", "title": "Paper 1"},
                {"id": "2", "title": "Paper 2"}
            ]
        }
        ```

        [total]: #total
        [nextCursor]: #nextcursor
    """

    def unwrap_results(self, response_json: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract the list of result items from an API response.

        This method should parse the API response and return the list of
        individual result items, regardless of how they are nested within
        the response structure.

        Args:
            response_json: The complete JSON response from the API as a dictionary.

        Returns:
            list[dict[str, Any]]: A list of dictionaries, where each dictionary
                represents a single result item from the API response.

        Raises:
            KeyError: If required response structure is missing.
            ValueError: If response format is invalid or unexpected.

        Example:
            For OpenAIRE: return response_json.get("results", [])
            For Crossref: return response_json.get("message", {}).get("items", [])
        """
        ...

    def unwrap_single_item(self, response_json: dict[str, Any]) -> dict[str, Any]:
        """Extract a single item from an API response.

        This method should parse the API response when it contains a single
        entity (e.g., from a GET /entities/{id} endpoint) and return that
        entity's data.

        Args:
            response_json: The complete JSON response from the API as a dictionary.

        Returns:
            dict[str, Any]: A dictionary containing the single result item's data.

        Raises:
            KeyError: If required response structure is missing.
            ValueError: If response format is invalid or contains no item.

        Example:
            For OpenAIRE: return response_json.get("results", [{}])[0]
            For Crossref: return response_json.get("message", {})
        """
        ...

    def get_next_page_token(self, response_json: dict[str, Any]) -> str | None:
        """Extract the pagination token for the next page from an API response.

        This method should parse the API response and return the token, cursor,
        or other identifier needed to fetch the next page of results. Returns
        None if there are no more pages available.

        Args:
            response_json: The complete JSON response from the API as a dictionary.

        Returns:
            str | None: The pagination token/cursor for the next page, or None
                if no more pages are available.

        Note:
            Different APIs use different pagination schemes:
            - Cursor-based: return a cursor string
            - Offset-based: return the next offset as a string
            - Page-based: return the next page number as a string
            - Link-based: extract the next URL and return relevant parts

        Example:
            For OpenAIRE: return response_json.get("header", {}).get("nextCursor")
            For Crossref: return str(current_offset + page_size) if has_more else None
        """
        ...

    def get_total_results(self, response_json: dict[str, Any]) -> int | None:
        """Extract the total count of results from an API response.

        This method should parse the API response and return the total number
        of results available across all pages, if this information is provided
        by the API. Returns None if the total count is not available.

        Args:
            response_json: The complete JSON response from the API as a dictionary.

        Returns:
            int | None: The total number of results across all pages, or None
                if this information is not available in the response.

        Note:
            Not all APIs provide total counts in their responses. Some only
            indicate whether more results are available without giving the
            exact total. In such cases, this method should return None.

        Example:
            For OpenAIRE: return response_json.get("header", {}).get("total")
            For Crossref: return response_json.get("message", {}).get("total-results")
        """
        ...
