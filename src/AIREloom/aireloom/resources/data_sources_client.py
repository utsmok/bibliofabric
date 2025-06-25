# aireloom/resources/data_sources_client.py
"""Client for interacting with OpenAIRE Data Sources."""

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import httpx
from bibliofabric.log_config import logger

if TYPE_CHECKING:
    from ..client import AireloomClient
from bibliofabric.exceptions import BibliofabricError, ValidationError

from ..constants import DEFAULT_PAGE_SIZE  # DATA_SOURCES is now in endpoints
from ..endpoints import (  # Import model
    DATA_SOURCES,
    ENDPOINT_DEFINITIONS,
    DataSourcesFilters,
)
from ..models import (
    ApiResponse,
    DataSource,
    DataSourceResponse,
)
from .base_client import BaseResourceClient


class DataSourcesClient(BaseResourceClient):
    """Provides methods to interact with OpenAIRE Data Sources."""

    _entity_path: str = DATA_SOURCES
    _entity_model: type[DataSource] = DataSource
    _response_model: type[DataSourceResponse] = DataSourceResponse

    def __init__(self, api_client: "AireloomClient"):
        """Initializes the DataSourcesClient.

        Args:
            api_client: An instance of AireloomClient.
        """
        super().__init__(api_client)
        if self._entity_path not in ENDPOINT_DEFINITIONS:
            raise ValueError(
                f"Missing endpoint definition for entity path: {self._entity_path}"
            )
        self._endpoint_def = ENDPOINT_DEFINITIONS[self._entity_path]
        self._valid_sort_fields = self._endpoint_def.get(
            "sort", {}
        ).keys()  # Get sort fields
        logger.debug(f"DataSourcesClient initialized for path: {self._entity_path}")

    # _validate_filters and _validate_and_convert_filter_value are removed as Pydantic handles this.

    def _validate_sort(self, sort_by: str | None) -> None:
        """Validates the sort field against endpoint definitions."""
        if not sort_by:
            return

        if not self._valid_sort_fields:
            logger.warning(
                f"Sort field '{sort_by}' provided for {self._entity_path}, "
                "but no sort fields are defined. Ignoring sort."
            )
            return
        sort_field_name = sort_by.split()[0]
        if sort_field_name not in self._valid_sort_fields:
            raise ValidationError(
                f"Invalid sort field for {self._entity_path}: '{sort_field_name}'. "
                f"Valid fields: {list(self._valid_sort_fields)}"
            )

    def _build_params(
        self,
        page: int | None,
        page_size: int,
        sort_by: str | None,
        filters: dict[str, Any] | None,  # Changed to Optional[dict]
        *,
        is_iteration: bool = False,
    ) -> dict[str, Any]:
        """Builds the query parameter dictionary."""
        params: dict[str, Any] = {"pageSize": page_size}
        if is_iteration:
            params["cursor"] = "*"
        elif page is not None:
            params["page"] = page
        if sort_by:
            params["sortBy"] = sort_by
        if filters:
            params.update(filters)
        return {k: v for k, v in params.items() if v is not None}

    async def _fetch_single_entity_impl(self, entity_id: str) -> DataSource:
        """Generic method to fetch a single entity by ID using search-by-ID."""
        try:
            # Use search with ID parameter instead of direct GET
            params = {"id": entity_id, "pageSize": 1}
            response = await self._api_client.request(
                "GET", self._entity_path, params=params, data=None, json_data=None
            )
            data = response.json()

            # Parse the search response
            search_response = self._response_model.model_validate(data)

            if not search_response.results:
                raise BibliofabricError(
                    f"{self._entity_model.__name__} with ID '{entity_id}' not found."
                )

            # Return the first (and should be only) result
            return search_response.results[0]

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTPStatusError for {self._entity_model.__name__} ID '{entity_id}': {e.response.status_code}"
            )
            raise BibliofabricError(
                f"API error fetching {self._entity_model.__name__} {entity_id}: "
                f"Status {e.response.status_code}"
            ) from e
        except Exception as e:
            if isinstance(e, BibliofabricError):
                raise
            logger.exception(
                f"Failed to fetch {self._entity_model.__name__} {entity_id} from {self._entity_path}"
            )
            raise BibliofabricError(
                f"Unexpected error fetching {self._entity_model.__name__} {entity_id}: {e}"
            ) from e

    async def _search_entities_impl(self, params: dict[str, Any]) -> DataSourceResponse:
        """Generic method to search for entities."""
        try:
            response = await self._api_client.request(
                "GET", self._entity_path, params=params, data=None, json_data=None
            )
            return self._response_model.model_validate(response.json())
        except Exception as e:
            if isinstance(e, BibliofabricError | ValidationError):
                raise
            logger.exception(
                f"Failed to search {self._entity_path} with params {params}"
            )
            raise BibliofabricError(
                f"Unexpected error searching {self._entity_path}: {e}"
            ) from e

    async def _iterate_entities_impl(
        self, params: dict[str, Any]
    ) -> AsyncIterator[DataSource]:
        """Generic method to iterate through all results using cursor pagination."""
        current_params = params.copy()
        while True:
            try:
                logger.debug(
                    f"Iterating {self._entity_path} with params: {current_params}"
                )
                response = await self._api_client.request(
                    "GET",
                    self._entity_path,
                    params=current_params,
                    data=None,
                    json_data=None,
                )
                data = response.json()
                api_response = ApiResponse[self._entity_model].model_validate(data)
                if not api_response.results:
                    logger.debug(
                        f"No more results for {self._entity_path}, stopping iteration."
                    )
                    break
                for result in api_response.results:
                    yield result
                next_cursor = api_response.header.nextCursor
                if not next_cursor:
                    logger.debug(
                        f"No nextCursor for {self._entity_path}, stopping iteration."
                    )
                    break
                current_params["cursor"] = next_cursor
                current_params.pop("page", None)
            except Exception as e:
                if isinstance(e, BibliofabricError | ValidationError):
                    raise
                logger.exception(
                    f"Failed during iteration of {self._entity_path} with params {current_params}"
                )
                raise BibliofabricError(
                    f"Unexpected error during iteration of {self._entity_path}: {e}"
                ) from e

    async def get(self, source_id: str) -> DataSource:
        """Retrieves a single Data Source by its ID.

        Args:
            source_id: The ID of the data source.

        Returns:
            A DataSource object.
        """
        logger.info(f"Fetching data source with ID: {source_id}")
        return await self._fetch_single_entity_impl(source_id)

    async def search(
        self,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        sort_by: str | None = None,
        filters: DataSourcesFilters | None = None,  # Changed to Pydantic model
    ) -> DataSourceResponse:
        """Searches for Data Sources.

        Args:
            page: Page number (1-indexed).
            page_size: Number of results per page.
            sort_by: Field to sort by.
            filters: An instance of DataSourcesFilters with filter criteria.

        Returns:
            A DataSourceResponse object.
        """
        filter_dict = (
            filters.model_dump(exclude_none=True, by_alias=True) if filters else {}
        )
        logger.info(
            f"Searching data sources: page={page}, size={page_size}, sort='{sort_by}', "
            f"filters={filter_dict}"
        )
        # self._validate_filters is removed
        self._validate_sort(sort_by)
        params = self._build_params(
            page=page, page_size=page_size, sort_by=sort_by, filters=filter_dict
        )
        return await self._search_entities_impl(params)

    async def iterate(
        self,
        page_size: int = 100,
        sort_by: str | None = None,
        filters: DataSourcesFilters | None = None,  # Changed to Pydantic model
    ) -> AsyncIterator[DataSource]:
        """Iterates through all Data Source results.

        Args:
            page_size: Number of results per page during iteration.
            sort_by: Field to sort by.
            filters: An instance of DataSourcesFilters with filter criteria.

        Yields:
            DataSource objects.
        """
        filter_dict = (
            filters.model_dump(exclude_none=True, by_alias=True) if filters else {}
        )
        logger.info(
            f"Iterating data sources: size={page_size}, sort='{sort_by}', "
            f"filters={filter_dict}"
        )
        # self._validate_filters is removed
        self._validate_sort(sort_by)
        params = self._build_params(
            page=None,
            page_size=page_size,
            sort_by=sort_by,
            filters=filter_dict,
            is_iteration=True,
        )
        async for item in self._iterate_entities_impl(params):
            yield item
