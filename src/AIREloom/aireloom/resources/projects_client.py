# aireloom/resources/projects_client.py
"""Client for interacting with the OpenAIRE Projects API endpoint.

This module provides the `ProjectsClient`, enabling access to OpenAIRE's
project data. It utilizes generic mixins from `bibliofabric.resources`
for standard API operations like fetching, searching, and iterating through
project entities.
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
from ..endpoints import PROJECTS
from ..models import Project, ProjectResponse


class ProjectsClient(
    GettableMixin, SearchableMixin, CursorIterableMixin, BaseResourceClient
):
    """Client for the OpenAIRE Projects API endpoint.

    This client offers standardized methods (`get`, `search`, `iterate`) for
    accessing project data by inheriting from `bibliofabric` mixins.
    It is configured with the API path and Pydantic models specific to
    OpenAIRE project entities.

    Attributes:
        _entity_path (str): The API path for projects.
        _entity_model (type[Project]): Pydantic model for a single project.
        _search_response_model (type[ProjectResponse]): Pydantic model for the
                                                        search response envelope.
        _valid_sort_fields (set[str]): Valid sort fields for this endpoint.
    """

    _entity_path: str = PROJECTS
    _entity_model: type[Project] = Project
    _search_response_model: type[ProjectResponse] = ProjectResponse
    _valid_sort_fields = {
        "acronym",
        "code",
        "enddate",
        "fundinglevel",
        "fundingtree",
        "id",
        "startdate",
        "title",
    }

    def __init__(self, api_client: "AireloomClient"):
        """Initializes the ProjectsClient.

        Args:
            api_client: An instance of AireloomClient.
        """
        super().__init__(api_client)
        logger.debug(f"ProjectsClient initialized for path: {self._entity_path}")

    # All get, search, and iterate methods are now provided by the mixins
