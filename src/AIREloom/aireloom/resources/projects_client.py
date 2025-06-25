# aireloom/resources/projects_client.py
"""Client for interacting with OpenAIRE Projects."""

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
    """Provides methods to interact with OpenAIRE Projects."""

    _entity_path: str = PROJECTS
    _entity_model: type[Project] = Project
    _search_response_model: type[ProjectResponse] = ProjectResponse

    def __init__(self, api_client: "AireloomClient"):
        """Initializes the ProjectsClient.

        Args:
            api_client: An instance of AireloomClient.
        """
        super().__init__(api_client)
        logger.debug(f"ProjectsClient initialized for path: {self._entity_path}")

    # All get, search, and iterate methods are now provided by the mixins
