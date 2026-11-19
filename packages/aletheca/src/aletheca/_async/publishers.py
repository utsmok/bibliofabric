"""Client for the OpenAlex publishers endpoint."""

from ..models import Publisher
from .dialect import OpenAlexResourceClient


class PublishersClient(OpenAlexResourceClient[Publisher]):
    """Client for the ``/publishers`` endpoint."""

    path = "publishers"
    model = Publisher
