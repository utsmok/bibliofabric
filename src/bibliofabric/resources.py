"""Generic resource mixins for the bibliofabric framework.

This module provides reusable base classes and mixins that abstract common API
resource operations like getting single entities, searching with pagination, and
cursor-based iteration. These mixins work with the BaseApiClient and
ResponseUnwrapper protocol to provide a consistent interface across different
API implementations.

The mixins are designed to be composable - a concrete resource client can inherit
from multiple mixins as needed to provide the appropriate functionality for that
specific resource type.
"""

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, Protocol

from pydantic import BaseModel

from .exceptions import BibliofabricError
from .log_config import logger

if TYPE_CHECKING:
    from .client import BaseApiClient
    from .models import ResponseUnwrapper


class ResourceClientProtocol(Protocol):
    """Protocol that defines the interface expected by resource mixins.

    This protocol ensures that classes using the mixins have the required
    attributes and methods that the mixins depend on.
    """

    _api_client: "BaseApiClient"
    _entity_path: str
    _entity_model: Any  # More flexible to handle any Pydantic model type
    _search_response_model: Any  # More flexible to handle any Pydantic model type

    @property
    def response_unwrapper(self) -> "ResponseUnwrapper": ...


class BaseResourceClient:
    """Base class for all resource clients in the bibliofabric framework.

    This class provides the foundation for resource clients by holding a
    reference to the main API client and providing access to the response
    unwrapper. All resource mixins expect to be used with this base class.

    Attributes:
        _api_client: The main API client instance for making HTTP requests.
        _entity_path: The API endpoint path for this resource (set by subclasses).
        _entity_model: Optional Pydantic model class for individual entities.
        _search_response_model: Optional Pydantic model class for search responses.
    """

    def __init__(self, api_client: "BaseApiClient"):
        """Initialize the base resource client.

        Args:
            api_client: An instance of BaseApiClient for making HTTP requests.
        """
        self._api_client = api_client
        logger.debug(f"{self.__class__.__name__} initialized")

    @property
    def response_unwrapper(self) -> "ResponseUnwrapper":
        """Get the response unwrapper from the API client.

        Returns:
            ResponseUnwrapper: The response unwrapper instance from the API client.
        """
        return self._api_client._response_unwrapper


class GettableMixin:
    """Mixin that provides generic get() functionality for retrieving single entities.

    This mixin implements a standard pattern for fetching individual entities by ID.
    It uses the search functionality with an ID filter since many APIs don't provide
    direct GET endpoints for individual resources.

    Classes using this mixin must inherit from BaseResourceClient and define:
    - _entity_path: The API endpoint path
    - _entity_model: The Pydantic model for the entity type (optional)
    """

    async def get(self: ResourceClientProtocol, entity_id: str) -> Any:
        """Retrieve a single entity by its ID.

        This method performs a search operation with the entity ID to fetch
        a single entity. It uses the response unwrapper to extract the entity
        data from the API response.

        Args:
            entity_id: The unique identifier of the entity to retrieve.

        Returns:
            Any: The entity data, either as a parsed Pydantic model (if _entity_model
                is defined) or as a raw dictionary.

        Raises:
            BibliofabricError: If the entity is not found or if the API request fails.
        """
        if not self._entity_path:
            raise BibliofabricError(
                f"{self.__class__.__name__} must define _entity_path"
            )

        logger.info(f"Fetching entity with ID: {entity_id}")

        try:
            # Use search with ID parameter instead of direct GET
            params = {"id": entity_id, "pageSize": 1}

            response = await self._api_client.request(
                "GET", self._entity_path, params=params
            )

            response_data = response.json()

            # Use the response unwrapper to get results
            results = self.response_unwrapper.unwrap_results(response_data)

            if not results:
                entity_name = (
                    self._entity_model.__name__ if self._entity_model else "Entity"
                )
                raise BibliofabricError(
                    f"{entity_name} with ID '{entity_id}' not found."
                )

            # Get the first (and should be only) result
            entity_data = results[0]

            # Parse with entity model if available
            if self._entity_model:
                try:
                    return self._entity_model.model_validate(entity_data)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse entity data with {self._entity_model.__name__}: {e}. "
                        "Returning raw data."
                    )
                    return entity_data

            return entity_data

        except Exception as e:
            if isinstance(e, BibliofabricError):
                raise
            logger.exception(
                f"Failed to fetch entity {entity_id} from {self._entity_path}"
            )
            raise BibliofabricError(
                f"Unexpected error fetching entity {entity_id}: {e}"
            ) from e


class SearchableMixin:
    """Mixin that provides generic search() functionality with pagination support.

    This mixin implements a standard pattern for searching entities with support
    for page-based pagination, filtering, and sorting. It uses the response
    unwrapper to handle API-specific response formats.

    Classes using this mixin must inherit from BaseResourceClient and define:
    - _entity_path: The API endpoint path
    - _search_response_model: The Pydantic model for search responses (optional)
    """

    async def search(
        self: ResourceClientProtocol,
        page: int = 1,
        page_size: int = 20,
        sort_by: str | None = None,
        filters: BaseModel | dict[str, Any] | None = None,
    ) -> Any:
        """Search for entities with pagination support.

        Args:
            page: Page number (1-indexed).
            page_size: Number of results per page.
            sort_by: Field to sort by (e.g., 'title asc', 'date desc').
            filters: Filter criteria as a Pydantic model or dictionary.

        Returns:
            Any: Search results, either as a parsed Pydantic model (if
                _search_response_model is defined) or as raw response data.

        Raises:
            BibliofabricError: If the API request fails.
        """
        if not self._entity_path:
            raise BibliofabricError(
                f"{self.__class__.__name__} must define _entity_path"
            )

        # Convert filters to dictionary if it's a Pydantic model
        filter_dict: dict[str, Any] = {}
        if filters:
            if isinstance(filters, BaseModel):
                filter_dict = filters.model_dump(exclude_none=True, by_alias=True)
            elif isinstance(filters, dict):
                filter_dict = filters
            else:
                raise BibliofabricError(
                    f"filters must be a Pydantic model or dictionary, got {type(filters)}"
                )

        logger.info(
            f"Searching {self._entity_path}: page={page}, size={page_size}, "
            f"sort='{sort_by}', filters={filter_dict}"
        )

        # Build query parameters
        params: dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
        }

        if sort_by:
            params["sortBy"] = sort_by

        if filter_dict:
            params.update(filter_dict)

        try:
            response = await self._api_client.request(
                "GET", self._entity_path, params=params
            )

            response_data = response.json()

            # Parse with search response model if available
            if self._search_response_model:
                try:
                    return self._search_response_model.model_validate(response_data)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse search response with {self._search_response_model.__name__}: {e}. "
                        "Returning raw data."
                    )
                    return response_data

            return response_data

        except Exception as e:
            if isinstance(e, BibliofabricError):
                raise
            logger.exception(
                f"Failed to search {self._entity_path} with params {params}"
            )
            raise BibliofabricError(
                f"Unexpected error searching {self._entity_path}: {e}"
            ) from e


class CursorIterableMixin:
    """Mixin that provides generic iterate() functionality using cursor-based pagination.

    This mixin implements a standard pattern for iterating through all results
    using cursor-based pagination. It handles the pagination loop automatically
    and yields individual entities as they are retrieved.

    Classes using this mixin must inherit from BaseResourceClient and define:
    - _entity_path: The API endpoint path
    - _entity_model: The Pydantic model for individual entities (optional)
    """

    async def iterate(
        self: ResourceClientProtocol,
        page_size: int = 100,
        sort_by: str | None = None,
        filters: BaseModel | dict[str, Any] | None = None,
    ) -> AsyncIterator[Any]:
        """Iterate through all entities matching the criteria using cursor pagination.

        This method automatically handles pagination by using cursors to fetch
        successive pages of results. It yields individual entities as they are
        retrieved from each page.

        Args:
            page_size: Number of results to fetch per API call during iteration.
            sort_by: Field to sort by.
            filters: Filter criteria as a Pydantic model or dictionary.

        Yields:
            Any: Individual entities, either as parsed Pydantic models (if
                _entity_model is defined) or as raw dictionaries.

        Raises:
            BibliofabricError: If the API request fails during iteration.
        """
        if not self._entity_path:
            raise BibliofabricError(
                f"{self.__class__.__name__} must define _entity_path"
            )

        # Convert filters to dictionary if it's a Pydantic model
        filter_dict: dict[str, Any] = {}
        if filters:
            if isinstance(filters, BaseModel):
                filter_dict = filters.model_dump(exclude_none=True, by_alias=True)
            elif isinstance(filters, dict):
                filter_dict = filters
            else:
                raise BibliofabricError(
                    f"filters must be a Pydantic model or dictionary, got {type(filters)}"
                )

        logger.info(
            f"Iterating {self._entity_path}: pageSize={page_size}, "
            f"sort='{sort_by}', filters={filter_dict}"
        )

        # Build initial parameters with cursor pagination
        params: dict[str, Any] = {
            "cursor": "*",  # Start cursor for iteration
            "pageSize": page_size,
        }

        if sort_by:
            params["sortBy"] = sort_by

        if filter_dict:
            params.update(filter_dict)

        while True:
            try:
                logger.debug(f"Iterating {self._entity_path} with params: {params}")

                response = await self._api_client.request(
                    "GET", self._entity_path, params=params
                )

                response_data = response.json()

                # Use the response unwrapper to get results and next cursor
                results = self.response_unwrapper.unwrap_results(response_data)
                next_cursor = self.response_unwrapper.get_next_page_token(response_data)

                if not results:
                    logger.debug(
                        f"No more results for {self._entity_path}, stopping iteration."
                    )
                    break

                # Yield each result
                for result_data in results:
                    # Parse with entity model if available
                    if self._entity_model:
                        try:
                            yield self._entity_model.model_validate(result_data)
                        except Exception as e:
                            logger.warning(
                                f"Failed to parse entity data with {self._entity_model.__name__}: {e}. "
                                "Yielding raw data."
                            )
                            yield result_data
                    else:
                        yield result_data

                # Check if there are more pages
                if not next_cursor:
                    logger.debug(
                        f"No nextCursor for {self._entity_path}, stopping iteration."
                    )
                    break

                # Update cursor for next iteration
                params["cursor"] = next_cursor
                # Remove page if it accidentally got in, cursor handles pagination
                params.pop("page", None)

            except Exception as e:
                if isinstance(e, BibliofabricError):
                    raise
                logger.exception(
                    f"Failed during iteration of {self._entity_path} with params {params}"
                )
                raise BibliofabricError(
                    f"Unexpected error during iteration of {self._entity_path}: {e}"
                ) from e
