"""Client for the OpenAlex awards endpoint."""

from ..models import Award
from .dialect import OpenAlexResourceClient


class AwardsClient(OpenAlexResourceClient[Award]):
    """Client for the ``/awards`` endpoint."""

    path = "awards"
    model = Award
