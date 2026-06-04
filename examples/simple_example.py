"""Minimal example: building an API client with bibliofabric.

This demonstrates the core pattern — implement ResponseUnwrapper for your
API, compose resource clients with mixins, and wire everything together.

For a complete, production-quality example, see the AIREloom project:
https://github.com/utsmok/aireloom
"""

import asyncio
from typing import Any

from pydantic import BaseModel

from bibliofabric.auth import NoAuth
from bibliofabric.client import BaseApiClient
from bibliofabric.config import BaseApiSettings
from bibliofabric.models import ResponseUnwrapper
from bibliofabric.resources import (
    BaseResourceClient,
    GettableMixin,
    SearchableMixin,
)


# ── 1. Define your API's data model ──────────────────────────────────────────


class Item(BaseModel):
    """A single item from the hypothetical API."""

    model_config = {"extra": "allow"}  # tolerate unknown fields

    id: str
    name: str


# ── 2. Implement ResponseUnwrapper for your API's response format ────────────


class SimpleApiUnwrapper(ResponseUnwrapper):
    """Teaches the framework how to parse this specific API's JSON responses."""

    def unwrap_results(self, response_json: dict[str, Any]) -> list[dict[str, Any]]:
        return response_json.get("data", [])

    def unwrap_single_item(self, response_json: dict[str, Any]) -> dict[str, Any]:
        return response_json.get("item", {})

    def get_next_page_token(self, response_json: dict[str, Any]) -> str | None:
        return response_json.get("cursor")

    def get_total_results(self, response_json: dict[str, Any]) -> int | None:
        return response_json.get("total")


# ── 3. Build resource clients using mixins ───────────────────────────────────


class ItemsClient(GettableMixin, SearchableMixin, BaseResourceClient):
    """Resource client for /items endpoint."""

    _entity_path: str = "items"
    _entity_model: type[BaseModel] | None = Item
    _search_response_model: type[BaseModel] | None = None


# ── 4. Create the top-level client ───────────────────────────────────────────


class SimpleApiClient(BaseApiClient):
    """Async client for the hypothetical SimpleAPI."""

    def __init__(self, settings: BaseApiSettings | None = None):
        settings = settings or BaseApiSettings()
        super().__init__(
            base_url="https://api.example.com/v1",
            settings=settings,
            auth_strategy=NoAuth(),
            response_unwrapper=SimpleApiUnwrapper(),
        )
        # Attach resource clients
        self.items = ItemsClient(api_client=self)


# ── 5. Use it ────────────────────────────────────────────────────────────────


async def main() -> None:
    async with SimpleApiClient() as client:
        # Get a single item by ID
        item = await client.items.get("item-42")
        print(f"Got item: {item}")

        # Search with pagination
        results = await client.items.search(params={"category": "books"})
        print(f"Found {len(results)} items")


if __name__ == "__main__":
    asyncio.run(main())
