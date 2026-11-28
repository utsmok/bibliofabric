"""Async Europe PMC resource clients; the sync twins are generated."""

from .annotations import AnnotationsClient
from .articles import ArticlesClient, split_article_id
from .client import EuropaeaClient
from .grants import GrantsClient
from .preprints import PPR_SOURCE, PreprintsClient
from .profiles import ProfilesClient
from .search import ResultType, SearchClient

__all__ = [
    "AnnotationsClient",
    "ArticlesClient",
    "PPR_SOURCE",
    "PreprintsClient",
    "ProfilesClient",
    "ResultType",
    "SearchClient",
    "EuropaeaClient",
    "split_article_id",
]
