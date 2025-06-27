# bibliofabric/types.py
"""Core type definitions and data structures for the bibliofabric framework.

This module defines common types used throughout the library, such as
data structures for request information and type aliases for request hooks.
"""

from collections.abc import Callable, Mapping
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field


class RequestData(BaseModel):
    """Encapsulates data for a single HTTP request attempt."""

    method: str
    url: str
    params: Mapping[str, Any] | None = None
    json_data: Any | None = None
    data: Mapping[str, Any] | None = None
    headers: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    def build_request(self) -> httpx.Request:
        """Builds an httpx.Request object from the stored data."""
        return httpx.Request(
            method=self.method,
            url=self.url,
            params=self.params,
            json=self.json_data,
            data=self.data,
            headers=self.headers,
        )


PreRequestHook = Callable[[str, str, dict[str, Any] | None, httpx.Headers], None]
"""Type alias for a pre-request hook.

Pre-request hooks are functions called before an HTTP request is sent.
They can be used to modify request parameters, headers, or perform other
actions like logging.

Args:
    method (str): The HTTP method of the request (e.g., "GET", "POST").
    url (str): The full URL of the request.
    params (dict[str, Any] | None): A mutable dictionary of query parameters.
        Hooks can modify this dictionary in place.
    headers (httpx.Headers): A mutable `httpx.Headers` object. Hooks can
        modify this object in place.
Return:
    None: Hooks are expected to modify arguments in-place or perform side effects.
"""

PostRequestHook = Callable[[httpx.Response, Any, int], None]
"""Type alias for a post-request hook.

Post-request hooks are functions called after an HTTP response is received
and processed (including potential parsing into a model). They can be used
for custom logging, response validation, or triggering further actions.

Args:
    response (httpx.Response): The raw `httpx.Response` object.
    parsed_model (Any): The response data parsed into a Pydantic model, if
        an `expected_model` was provided to the request and parsing was successful.
        Otherwise, this will be `None`.
    attempts (int): The number of attempts made to get a successful response.
Return:
    None: Hooks are expected to perform side effects.
"""
