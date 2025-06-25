# aireloom/resources/research_products_client.py
"""Client for interacting with OpenAIRE Research Products."""

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
    """Provides methods to interact with OpenAIRE Research Products."""

    _entity_path: str = RESEARCH_PRODUCTS
    _entity_model: type[ResearchProduct] = ResearchProduct
    _search_response_model: type[ResearchProductResponse] = ResearchProductResponse

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
