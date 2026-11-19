"""Client for the OpenAlex topics endpoint."""

from ..models import Topic
from .dialect import OpenAlexResourceClient


class TopicsClient(OpenAlexResourceClient[Topic]):
    """Client for the ``/topics`` endpoint."""

    path = "topics"
    model = Topic
