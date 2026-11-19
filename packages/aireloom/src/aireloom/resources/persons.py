"""Resource client for OpenAIRE persons (V4)."""

from ..filters import PersonsFilters
from ..models import Person
from .base import GraphResource


class PersonsResource(GraphResource[Person]):
    """V4 persons endpoint: search, iterate, count, facets, group_by.

    ``get(id)`` reads the V3 by-id route because V4 has no by-id endpoints.
    """

    path = "v4/persons"
    model = Person
    filters_model = PersonsFilters
