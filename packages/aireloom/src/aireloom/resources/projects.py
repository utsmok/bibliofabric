"""Resource client for OpenAIRE projects (V4)."""

from ..filters import ProjectsFilters
from ..models import Project
from .base import GraphResource


class ProjectsResource(GraphResource[Project]):
    """V4 projects endpoint: search, iterate, count, facets, group_by.

    ``get(id)`` reads the V3 by-id route because V4 has no by-id endpoints.
    """

    path = "v4/projects"
    model = Project
    filters_model = ProjectsFilters
    sort_fields = frozenset({"relevance", "start_date", "end_date"})
