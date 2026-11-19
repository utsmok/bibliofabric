"""Client for the OpenAlex institutions endpoint."""

from ..models import Institution
from .dialect import OpenAlexResourceClient


class InstitutionsClient(OpenAlexResourceClient[Institution]):
    """Client for the ``/institutions`` endpoint."""

    path = "institutions"
    model = Institution
