# aireloom/resources/scholix_client.py
"""Client for interacting with OpenAIRE Scholix (Scholexplorer) API."""

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from bibliofabric.log_config import logger

if TYPE_CHECKING:
    from ..client import AireloomClient
from bibliofabric.exceptions import BibliofabricError, ValidationError

from ..constants import (  # SCHOLIX is now in endpoints
    DEFAULT_PAGE_SIZE,
    OPENAIRE_SCHOLIX_API_BASE_URL,
)
from ..endpoints import ENDPOINT_DEFINITIONS, SCHOLIX, ScholixFilters  # Import model
from ..models import (
    ScholixRelationship,
    ScholixResponse,
)
from .base_client import BaseResourceClient


class ScholixClient(BaseResourceClient):
    """Provides methods to interact with the OpenAIRE Scholexplorer API."""

    _entity_path: str = (
        SCHOLIX  # This is the endpoint path, not an entity type like others
    )

    def __init__(
        self, api_client: "AireloomClient", scholix_base_url: str | None = None
    ):
        """Initializes the ScholixClient.

        Args:
            api_client: An instance of AireloomClient.
            scholix_base_url: Base URL for the Scholexplorer API.
        """
        super().__init__(api_client)
        self._scholix_base_url = scholix_base_url or OPENAIRE_SCHOLIX_API_BASE_URL
        if self._entity_path not in ENDPOINT_DEFINITIONS:
            raise ValueError(
                f"Missing endpoint definition for Scholix path: {self._entity_path}"
            )
        self._endpoint_def = ENDPOINT_DEFINITIONS[self._entity_path]
        # Scholix does not have sort fields defined in ENDPOINT_DEFINITIONS
        logger.debug(
            f"ScholixClient initialized for base URL: {self._scholix_base_url}"
        )

    # _validate_filters and _validate_and_convert_filter_value are removed as Pydantic handles this.
    # Scholix API has specific PID requirements handled in search_links.

    def _build_scholix_params(
        self,
        page: int,  # Scholix is 0-indexed
        page_size: int,
        filters: dict[str, Any] | None,  # Changed to Optional[dict]
    ) -> dict[str, Any]:
        """Builds the query parameter dictionary for Scholix API."""
        # Scholix uses 'rows' for page_size and 0-indexed 'page'
        params = {"page": page, "rows": page_size}
        if filters:
            params.update(filters)
        return {k: v for k, v in params.items() if v is not None}

    async def search_links(
        self,
        page: int = 0,  # Scholix default is 0-indexed
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: ScholixFilters | None = None,  # Changed to Pydantic model
    ) -> ScholixResponse:
        """Searches for Scholexplorer relationship links.

        Args:
            page: The page number to retrieve (0-indexed).
            page_size: The number of results per page.
            filters: An instance of ScholixFilters with filter criteria.
                       `sourcePid` or `targetPid` is typically required within the model.

        Returns:
            A ScholixResponse object containing the results for the requested page.

        Raises:
            ValueError: If neither sourcePid nor targetPid is provided in the filters model.
            BibliofabricError: For API communication errors or unexpected issues.
        """
        filter_dict = (
            filters.model_dump(exclude_none=True, by_alias=True) if filters else {}
        )
        logger.info(
            f"Searching Scholix links: page={page}, size={page_size}, filters={filter_dict}"
        )

        if not filter_dict.get("sourcePid") and not filter_dict.get("targetPid"):
            raise ValueError(
                "Either sourcePid or targetPid must be provided for Scholix search within the filters."
            )

        # Pydantic model validation happens at instantiation or via .model_validate()
        # No need for self._validate_filters(filter_dict) here.

        params = self._build_scholix_params(
            page=page, page_size=page_size, filters=filter_dict
        )

        try:
            response = await self._api_client.request(
                method="GET",
                path=self._entity_path,  # SCHOLIX constant
                params=params,
                base_url_override=self._scholix_base_url,
                data=None,
                json_data=None,
            )
            return ScholixResponse.model_validate(response.json())
        except Exception as e:
            if isinstance(
                e, BibliofabricError | ValidationError
            ):  # ValidationError can come from Pydantic
                raise
            logger.exception(
                f"Failed to search {self._entity_path} with params {params} at {self._scholix_base_url}"
            )
            raise BibliofabricError(
                f"Unexpected error searching {self._entity_path}: {e}"
            ) from e

    async def iterate_links(
        self,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: ScholixFilters | None = None,  # Changed to Pydantic model
    ) -> AsyncIterator[ScholixRelationship]:
        """Iterates through all Scholexplorer relationship links matching the filters.

        Handles pagination automatically based on 'total_pages'.

        Args:
            page_size: The number of results per page during iteration.
            filters: An instance of ScholixFilters with filter criteria.
                       `sourcePid` or `targetPid` is typically required.

        Yields:
            ScholixRelationship objects matching the query.

        Raises:
            ValueError: If neither sourcePid nor targetPid is provided in the filters.
            BibliofabricError: For API communication errors or unexpected issues.
        """
        # The Pydantic model (ScholixFilters) will be passed to search_links,
        # which now expects the model instance.
        logger.info(
            f"Iterating Scholix links: size={page_size}, filters provided: {filters is not None}"
        )

        current_page = 0
        total_pages = 1  # Assume at least one page initially

        while current_page < total_pages:
            logger.debug(
                f"Iterating Scholix page {current_page + 1}/{total_pages if total_pages > 1 else '?'}"
            )
            try:
                # search_links now takes the ScholixFilters model directly
                response_data = await self.search_links(
                    page=current_page,
                    page_size=page_size,
                    filters=filters,
                )

                if not response_data.result:
                    logger.debug(
                        "No results found on this Scholix page, stopping iteration."
                    )
                    break

                for link in response_data.result:
                    yield link

                if current_page == 0:  # Only update total_pages on the first call
                    total_pages = response_data.total_pages
                    logger.debug(f"Total pages reported by Scholix: {total_pages}")
                    if total_pages == 0:  # No results at all
                        logger.debug(
                            "Scholix reported 0 total pages. Stopping iteration."
                        )
                        break

                if current_page >= total_pages - 1:
                    logger.debug("Last Scholix page processed, stopping iteration.")
                    break

                current_page += 1

            except Exception as e:
                if isinstance(e, BibliofabricError | ValidationError):
                    raise
                logger.exception(
                    f"Failed during iteration of {self._entity_path} on page {current_page}"
                )
                raise BibliofabricError(
                    f"Failed during iteration of {self._entity_path} on page {current_page}: {e}"
                ) from e
        logger.debug("Scholix iteration finished.")
