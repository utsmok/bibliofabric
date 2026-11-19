"""Client for the OpenAlex keywords endpoint."""

from ..models import Keyword
from .dialect import OpenAlexResourceClient


class KeywordsClient(OpenAlexResourceClient[Keyword]):
    """Client for the ``/keywords`` endpoint."""

    path = "keywords"
    model = Keyword
