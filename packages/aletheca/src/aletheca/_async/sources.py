"""Client for the OpenAlex sources endpoint."""

from ..models import Source
from .dialect import OpenAlexResourceClient


class SourcesClient(OpenAlexResourceClient[Source]):
    """Client for the ``/sources`` endpoint."""

    path = "sources"
    model = Source
