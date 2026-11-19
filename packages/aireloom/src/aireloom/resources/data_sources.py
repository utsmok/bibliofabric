"""Resource client for OpenAIRE data sources (V4)."""

from ..filters import DataSourcesFilters
from ..models import DataSource
from .base import GraphResource


class DataSourcesResource(GraphResource[DataSource]):
    """V4 data sources endpoint: search, iterate, count, facets, group_by.

    ``get(id)`` reads the V3 by-id route because V4 has no by-id endpoints.
    """

    path = "v4/datasources"
    model = DataSource
    filters_model = DataSourcesFilters
