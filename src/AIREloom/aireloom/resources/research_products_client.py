# aireloom/resources/research_products_client.py
"""Client for interacting with the OpenAIRE Research Products API endpoint.

This module provides the `ResearchProductsClient`, which facilitates access to
OpenAIRE's research product data (e.g., publications, datasets, software).
It leverages generic mixins from `bibliofabric.resources` for common API
operations like retrieving individual entities, searching, and iterating
through result sets.
"""

from typing import TYPE_CHECKING

from bibliofabric.log_config import logger
from bibliofabric.resources import (
    BaseResourceClient,
    CursorIterableMixin,
    GettableMixin,
    SearchableMixin,
)

if TYPE_CHECKING:
    from ..client import AireloomClient
from ..endpoints import RESEARCH_PRODUCTS
from ..models import ResearchProduct, ResearchProductResponse


class ResearchProductsClient(
    GettableMixin, SearchableMixin, CursorIterableMixin, BaseResourceClient
):
    """Client for the OpenAIRE Research Products API endpoint.

    This client provides standardized methods (`get`, `search`, `iterate`) for
    accessing research product data, by inheriting from `bibliofabric` mixins.
    It is configured with the specific API path and Pydantic models relevant
    to OpenAIRE research products.

    Attributes:
        _entity_path (str): The API path for research products.
        _entity_model (type[ResearchProduct]): Pydantic model for a single research product.
        _search_response_model (type[ResearchProductResponse]): Pydantic model for the
                                                                search response envelope.
        _valid_sort_fields (set[str]): A set of field names that are valid for sorting
                                       results from this endpoint.
    """

    _entity_path: str = RESEARCH_PRODUCTS
    _entity_model: type[ResearchProduct] = ResearchProduct
    _search_response_model: type[ResearchProductResponse] = ResearchProductResponse
    _valid_sort_fields = {
        "bestaccessright",
        "publicationdate",
        "relevance",
        "title",
    }

    def __init__(self, api_client: "AireloomClient"):
        """Initializes the ResearchProductsClient.

        Args:
            api_client: An instance of AireloomClient.
        """
        super().__init__(api_client)
        logger.debug(
            f"ResearchProductsClient initialized for path: {self._entity_path}"
        )

    # All get, search, and iterate methods are now provided by the mixins
    # The mixins automatically handle:
    # - Generic HTTP requests through the api_client
    # - Response unwrapping through the response_unwrapper
    # - Pydantic model parsing and error handling
    # - Cursor-based and page-based pagination
    # - Filter conversion from Pydantic models to dictionaries
