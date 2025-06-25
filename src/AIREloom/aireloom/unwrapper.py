# aireloom/unwrapper.py
"""OpenAIRE-specific response unwrapper implementation.

This module provides the OpenAIRE implementation of the ResponseUnwrapper
protocol from bibliofabric, enabling the generic framework to work with
OpenAIRE's specific JSON response structure.
"""

from typing import Any

from bibliofabric.models import ResponseUnwrapper


class OpenAireUnwrapper(ResponseUnwrapper):
    """OpenAIRE-specific implementation of the ResponseUnwrapper protocol.

    This class handles the specific JSON response structure used by OpenAIRE APIs,
    which typically follow this pattern:

    ```json
    {
        "header": {
            "numFound": 1000,
            "nextCursor": "abc123",
            "queryTime": 50,
            "pageSize": 10
        },
        "results": [
            {"id": "1", "title": "Paper 1"},
            {"id": "2", "title": "Paper 2"}
        ]
    }
    ```

    The unwrapper extracts the relevant information from this structure
    to enable generic pagination and result handling in the bibliofabric framework.
    """

    def unwrap_results(self, response_json: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract the list of result items from an OpenAIRE API response.

        OpenAIRE APIs return results in a top-level "results" array.
        If the "results" key is missing or None, returns an empty list
        to handle edge cases gracefully.

        Args:
            response_json: The complete JSON response from the OpenAIRE API.

        Returns:
            list[dict[str, Any]]: A list of result items, or empty list if none found.

        Raises:
            ValueError: If response_json is None or not a dictionary.
        """
        if response_json is None:
            raise ValueError("Response JSON cannot be None")
        if not isinstance(response_json, dict):
            raise ValueError(
                f"Response JSON must be a dictionary, got {type(response_json)}"
            )

        results = response_json.get("results")
        if results is None:
            return []
        if not isinstance(results, list):
            raise ValueError(f"Expected results to be a list, got {type(results)}")

        return results

    def unwrap_single_item(self, response_json: dict[str, Any]) -> dict[str, Any]:
        """Extract a single item from an OpenAIRE API response.

        For single-item requests (like GET by ID), OpenAIRE typically returns
        the item as the first element in the "results" array. This method
        extracts that first item.

        Args:
            response_json: The complete JSON response from the OpenAIRE API.

        Returns:
            dict[str, Any]: The single result item's data.

        Raises:
            ValueError: If response_json is invalid, no results found, or results is empty.
        """
        if response_json is None:
            raise ValueError("Response JSON cannot be None")
        if not isinstance(response_json, dict):
            raise ValueError(
                f"Response JSON must be a dictionary, got {type(response_json)}"
            )

        results = self.unwrap_results(response_json)
        if not results:
            raise ValueError("No results found in response for single item request")

        return results[0]

    def get_next_page_token(self, response_json: dict[str, Any]) -> str | None:
        """Extract the pagination token for the next page from an OpenAIRE API response.

        OpenAIRE uses cursor-based pagination with a "nextCursor" field in the
        response header. If no nextCursor is present, there are no more pages.

        Args:
            response_json: The complete JSON response from the OpenAIRE API.

        Returns:
            str | None: The next page cursor token, or None if no more pages.

        Note:
            Returns None for any errors in parsing rather than raising exceptions,
            as missing pagination info should not break the request flow.
        """
        if not isinstance(response_json, dict):
            return None

        header = response_json.get("header")
        if not isinstance(header, dict):
            return None

        next_cursor = header.get("nextCursor")
        if next_cursor is None:
            return None

        # Handle case where nextCursor might be an empty string
        if isinstance(next_cursor, str) and next_cursor.strip():
            return next_cursor.strip()

        # Handle potential URL objects or other types by converting to string
        try:
            cursor_str = str(next_cursor).strip()
            return cursor_str if cursor_str else None
        except Exception:
            return None

    def get_total_results(self, response_json: dict[str, Any]) -> int | None:
        """Extract the total count of results from an OpenAIRE API response.

        OpenAIRE typically provides the total number of available results
        in the "numFound" field within the response header. This is useful
        for pagination and progress tracking.

        Args:
            response_json: The complete JSON response from the OpenAIRE API.

        Returns:
            int | None: The total number of results across all pages, or None
                if this information is not available.

        Note:
            Returns None for any errors in parsing rather than raising exceptions,
            as missing total count should not break the request flow.
        """
        if not isinstance(response_json, dict):
            return None

        header = response_json.get("header")
        if not isinstance(header, dict):
            return None

        num_found = header.get("numFound")
        if num_found is None:
            return None

        # Handle string representations of numbers (common in APIs)
        if isinstance(num_found, str):
            try:
                return int(num_found)
            except (ValueError, TypeError):
                return None

        # Handle integer values
        if isinstance(num_found, int):
            return num_found

        # Handle other numeric types by attempting conversion
        try:
            return int(num_found)
        except (ValueError, TypeError, AttributeError):
            return None
