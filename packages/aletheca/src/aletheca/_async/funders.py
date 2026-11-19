"""Client for the OpenAlex funders endpoint."""

from ..models import Funder
from .dialect import OpenAlexResourceClient


class FundersClient(OpenAlexResourceClient[Funder]):
    """Client for the ``/funders`` endpoint."""

    path = "funders"
    model = Funder
