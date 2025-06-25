# bibliofabric/types.py
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


PreRequestHook = Callable[[str, str, dict[str, Any] | None, httpx.Headers | None], None]
# Args: method, url, params, headers
# Return: None (hooks modify in place or trigger side effects)

PostRequestHook = Callable[[httpx.Response, Any], None]
# Args: httpx_response, parsed_response_model
# Return: None
